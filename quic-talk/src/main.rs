//! Markdown -> self-contained HTML slide deck.
//!
//! Usage: cargo run [-- input.md [output.html]]
//!
//! Slides are separated by lines containing only `---`. Images referencing
//! local SVG files are inlined into the page so the result is a single file
//! (PNG and JPEG images become data URIs);
//! SMIL animations keep working and are restarted whenever a slide becomes
//! active. All SVG ids are prefixed per slide so animations that reuse id
//! names (e.g. `#relay-path`) don't clash within the one document.

use pulldown_cmark::{html, CodeBlockKind, Event, Options, Parser, Tag, TagEnd};
use regex::Regex;
use std::fs;
use std::path::Path;
use syntect::highlighting::ThemeSet;
use syntect::html::highlighted_html_for_string;
use syntect::parsing::SyntaxSet;

fn main() {
    let mut args = std::env::args().skip(1);
    let input = args.next().unwrap_or_else(|| "index.md".into());
    let output = args.next().unwrap_or_else(|| "docs/index.html".into());

    let src = fs::read_to_string(&input)
        .unwrap_or_else(|e| panic!("cannot read {input}: {e}"));
    let base_dir = Path::new(&input).parent().unwrap_or(Path::new("."));

    let ss = SyntaxSet::load_defaults_newlines();
    let theme = &ThemeSet::load_defaults().themes["InspiredGitHub"];

    let slides: Vec<&str> = src
        .split("\n---")
        .map(|s| s.strip_prefix('\n').unwrap_or(s))
        .collect();

    // Reference-style link definitions (`[slug]: url`) are shared across the
    // whole file, even though each slide is rendered as its own document.
    let linkdefs: String = src
        .lines()
        .filter(|l| Regex::new(r"^\[[^\]]+\]:\s+\S").unwrap().is_match(l))
        .collect::<Vec<_>>()
        .join("\n");

    let title = src
        .lines()
        .find_map(|l| l.strip_prefix("# "))
        .unwrap_or("presentation")
        .to_string();

    let img_re = Regex::new(r#"<img src="([^"]+\.svg)" alt="([^"]*)"[^>]*>"#).unwrap();
    let raster_re =
        Regex::new(r#"<img src="([^"]+\.(png|jpe?g))" alt="([^"]*)"[^>]*>"#).unwrap();
    let mut body = String::new();
    for (idx, slide_md) in slides.iter().enumerate() {
        let with_defs = format!("{slide_md}\n\n{linkdefs}\n");
        let mut rendered = render_markdown(&with_defs, &ss, theme);
        rendered = img_re
            .replace_all(&rendered, |caps: &regex::Captures| {
                let path = base_dir.join(&caps[1]);
                let width = caps[2].strip_prefix("w:").and_then(|w| w.parse::<u32>().ok());
                match fs::read_to_string(&path) {
                    Ok(svg) => inline_svg(&svg, idx, width),
                    Err(e) => {
                        eprintln!("warning: cannot inline {}: {e}", path.display());
                        caps[0].to_string()
                    }
                }
            })
            .into_owned();
        rendered = raster_re
            .replace_all(&rendered, |caps: &regex::Captures| {
                let path = base_dir.join(&caps[1]);
                let mime = if &caps[2] == "png" { "image/png" } else { "image/jpeg" };
                let style = match caps[3].strip_prefix("w:").and_then(|w| w.parse::<u32>().ok()) {
                    Some(w) => format!(" style=\"width:{w}px\""),
                    None => String::new(),
                };
                match fs::read(&path) {
                    Ok(bytes) => format!("<img src=\"data:{mime};base64,{}\"{style}>", base64(&bytes)),
                    Err(e) => {
                        eprintln!("warning: cannot inline {}: {e}", path.display());
                        caps[0].to_string()
                    }
                }
            })
            .into_owned();
        let class = if idx == 0 {
            "slide title"
        } else if slide_md.contains("<!-- center -->") {
            "slide center"
        } else {
            "slide"
        };
        body.push_str(&format!("<section class=\"{class}\">\n{rendered}\n</section>\n"));
    }

    let page = format!(
        "<!doctype html>\n<html><head><meta charset=\"utf-8\">\n\
         <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n\
         <title>{title}</title>\n<style>{css}</style></head>\n\
         <body>\n{body}\n<div id=\"counter\"></div>\n<script>{js}</script>\n</body></html>\n",
        css = CSS,
        js = JS,
    );
    fs::write(&output, &page).unwrap_or_else(|e| panic!("cannot write {output}: {e}"));
    println!("{output}: {} slides, {} bytes", slides.len(), page.len());
}

/// Render one slide of markdown, highlighting fenced code blocks at build time.
fn render_markdown(md: &str, ss: &SyntaxSet, theme: &syntect::highlighting::Theme) -> String {
    let mut events = Vec::new();
    let mut code = String::new();
    let mut lang: Option<String> = None;
    for ev in Parser::new_ext(md, Options::ENABLE_TABLES | Options::ENABLE_STRIKETHROUGH) {
        match ev {
            Event::Start(Tag::CodeBlock(CodeBlockKind::Fenced(l))) => {
                lang = Some(l.to_string());
                code.clear();
            }
            Event::Text(t) if lang.is_some() => code.push_str(&t),
            Event::End(TagEnd::CodeBlock) if lang.is_some() => {
                let l = lang.take().unwrap();
                let syntax = ss
                    .find_syntax_by_token(&l)
                    .unwrap_or_else(|| ss.find_syntax_plain_text());
                let html = highlighted_html_for_string(&code, ss, syntax, theme)
                    .unwrap_or_else(|_| format!("<pre>{}</pre>", &code));
                events.push(Event::Html(html.into()));
            }
            ev => events.push(ev),
        }
    }
    let mut out = String::new();
    html::push_html(&mut out, events.into_iter());
    out
}

/// Standard base64 with padding, for data URIs.
fn base64(bytes: &[u8]) -> String {
    const ALPHABET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let n = chunk.iter().enumerate().fold(0u32, |n, (i, &b)| n | (b as u32) << (16 - 8 * i));
        for i in 0..4 {
            if i <= chunk.len() {
                out.push(ALPHABET[(n >> (18 - 6 * i) & 63) as usize] as char);
            } else {
                out.push('=');
            }
        }
    }
    out
}

/// Prepare an SVG for inlining: drop the XML prolog, prefix all ids and
/// id references with the slide index, and tag it with a class for styling.
/// An alt text of `w:NNN` in the markdown pins the display width in px.
fn inline_svg(svg: &str, slide: usize, width: Option<u32>) -> String {
    let mut s = svg.trim().to_string();
    if let Some(pos) = s.find("<svg") {
        s = s[pos..].to_string();
    }
    let p = format!("s{slide}-");
    s = Regex::new(r#"id=""#).unwrap().replace_all(&s, format!(r#"id="{p}"#)).into_owned();
    s = Regex::new(r##"href="#"##).unwrap().replace_all(&s, format!(r##"href="#{p}"##)).into_owned();
    s = Regex::new(r#"url\(#"#).unwrap().replace_all(&s, format!("url(#{p}")).into_owned();
    match width {
        Some(w) => s.replacen("<svg", &format!("<svg class=\"anim\" style=\"width:{w}px\""), 1),
        None => s.replacen("<svg", "<svg class=\"anim\"", 1),
    }
}

const CSS: &str = r#"
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; background: #1a1a1a; overflow: hidden; }
.slide {
  display: none; position: absolute; left: 50%; top: 50%;
  width: 1280px; height: 720px; padding: 48px 72px;
  background: #ffffff; color: #111;
  font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
  font-size: 28px; line-height: 1.45;
}
.slide.active { display: block; }
.slide.title, .slide.center { text-align: center; }
.slide.title.active, .slide.center.active { display: flex; flex-direction: column; justify-content: center; }
h1 { font-size: 64px; margin: 0 0 24px; }
.slide:not(.title) h1 { font-size: 44px; margin: 0 0 20px; }
h2 { font-size: 34px; }
li { margin: 8px 0; }
a { color: #6366f1; }
code { font-family: 'Space Mono', ui-monospace, monospace; font-size: 0.85em;
       background: #f3f4f6; padding: 1px 6px; border-radius: 4px; }
pre code, pre { background: none; }
pre { font-size: 20px; line-height: 1.4; margin: 12px 0; }
svg.anim { display: block; width: 100%; max-height: 530px; margin: 8px auto 0; }
img { max-width: 100%; max-height: 530px; display: block; margin: 8px auto 0; }
.bg { color: #6366f1; font-size: 0.8em; margin-left: 12px; white-space: nowrap; }
table { border-collapse: collapse; margin: 8px 0 16px; }
th, td { padding: 8px 28px 8px 0; text-align: left; vertical-align: top; }
thead th { border-bottom: 2px solid #ddd; }
tbody td { border-bottom: 1px solid #eee; }
#counter {
  position: fixed; right: 16px; bottom: 12px; color: #888;
  font-family: ui-monospace, monospace; font-size: 14px; z-index: 10;
}
/* PDF export: print via Chrome, one 1280x720 page per slide. */
@page { size: 1280px 720px; margin: 0; }
@media print {
  html, body { background: #fff; overflow: visible; height: auto; }
  .slide {
    display: block !important; position: static;
    transform: none !important; break-after: page; break-inside: avoid;
  }
  .slide.title, .slide.center {
    display: flex !important; flex-direction: column; justify-content: center;
  }
  #counter { display: none; }
}
"#;

const JS: &str = r#"
const slides = [...document.querySelectorAll('.slide')];
const counter = document.getElementById('counter');
let cur = Math.min(slides.length - 1, Math.max(0, parseInt(location.hash.slice(1)) || 0));

function rescale() {
  const s = Math.min(innerWidth / 1280, innerHeight / 720);
  for (const el of slides) {
    el.style.transform = `translate(-50%, -50%) scale(${s})`;
  }
}

function show(n) {
  n = Math.max(0, Math.min(slides.length - 1, n));
  slides[cur].classList.remove('active');
  cur = n;
  slides[cur].classList.add('active');
  history.replaceState(null, '', '#' + cur);
  counter.textContent = `${cur + 1} / ${slides.length}`;
  // restart SMIL animations so each slide's story begins at t=0
  for (const svg of slides[cur].querySelectorAll('svg')) {
    try { svg.setCurrentTime(0); } catch (e) {}
  }
}

addEventListener('keydown', (e) => {
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ' || e.key === 'PageDown') { e.preventDefault(); show(cur + 1); }
  else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp' || e.key === 'PageUp') { e.preventDefault(); show(cur - 1); }
  else if (e.key === 'Home') show(0);
  else if (e.key === 'End') show(slides.length - 1);
  else if (e.key === 'f') document.documentElement.requestFullscreen();
  else if (e.key === 'r') show(cur); // restart animations on current slide
});
addEventListener('click', (e) => {
  if (e.target.closest('a')) return;
  show(e.clientX > innerWidth / 2 ? cur + 1 : cur - 1);
});
addEventListener('resize', rescale);
rescale();
show(cur);
"#;
