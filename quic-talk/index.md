<!-- center -->

# Why iroh uses QUIC

Rüdiger Klaehn

n0.computer

---

<!-- center -->

iroh is a library for **direct** **QUIC** connections between endpoints identified and encrypted using ed25519 **keypairs**

---

<!-- center -->

iroh is **QUIC**, but **p2p**

---

# Iroh is p2p QUIC

- a library for **direct QUIC connections**
- works pretty much everywhere
- Rust, with bindings for C, C++, JS, Python, Swift, Go
- Browser works with caveats, but isn't main focus

![w:1050](public/animations/embedding-phone.svg)

---

# What makes iroh QUIC connections p2p?

- dial by **key**
- **direct** connections via hole punching

---

![](public/animations/routing-moves.svg)

---

# Picking a home relay

![](public/animations/endpoint-startup.svg)

---

# Address lookup: DNS

![](public/animations/publish-relay.svg)

---

# Address lookup: BitTorrent Mainline DHT

![](public/animations/publish-relay-dht.svg)

---

# Address lookup: mDNS

![](public/animations/mdns-address-lookup.svg)

---

# Hole punching

![](public/animations/hole-punching.svg)

---

# Iroh architecture

![](public/animations/layer-stack.svg)

---

# Why iroh uses QUIC

- Why QUIC on the wire?
  - Tailscale, Headscale (WG + disco)
  - NetBird, Firezone (WG + ICE)
  - Netmaker, innernet, Talos KubeSpan (WG)
  - ZeroTier (own protocol), Nebula (Noise)
- Why QUIC as the iroh API?
  - [HTTP/3]: QUIC on the wire, HTTP API
  - [MASQUE]: QUIC on the wire, VPN/proxy API

---

# Why a QUIC API?

- No head of the line blocking between streams
- Stream priorities
- QUIC streams are very cheap

![](public/animations/connection-streams.svg)

---

# Why a QUIC API?

- Not a new abstraction: a real QUIC connection
- Protocols built on QUIC run on iroh directly, e.g. [Media over QUIC] (IETF WG)
- Reliable streams and unreliable datagrams on one connection
- One ALPN per protocol: many protocols on one endpoint
- Same API whether direct, relayed, or switching paths

---

# Why QUIC on the wire?

- QUIC multipath ([approved draft RFC])
- Congestion controllers *per path*
- No "relearning" during path switches
- CC provide info for path selection

![](public/animations/congestion-paths.svg)

---

# Hole punching

- QUIC extension `N0NatTraversal`
- Inspired by [Using QUIC to traverse NATs] draft RFC
- `N0NatTraversal` coordination frame types
  - `AddAddress` — advertise a candidate address
  - ~~`PunchMeNow`~~ `ReachOut` — punch towards this address now
  - `RemoveAddress` — retract a candidate address
- The punching itself is standard QUIC path validation: `PathChallenge` / `PathResponse`

---

# Why hole punching inside QUIC?

- One set of cryptographic primitives
- Use QUIC retransmit logic for coordination frames
- HP frames invisible to middleboxes

---

# Why QUIC address discovery (QAD) instead of STUN?

- We already do QUIC connections
- Responses encrypted - untouchable by middleboxes
- Responses authenticated - not spoofable

---

# What a middlebox sees

![](public/animations/packet-headers.svg)

---

# QUIC as the API, QUIC on the wire

- Dial a **key**, not an address: address lookup finds the endpoint
- QUIC API: cheap streams, no head-of-line blocking, priorities
- QUIC wire: multipath, hole punching and address discovery inside the connection
- To a middlebox, it's just QUIC
- Higher level protocols on top: [iroh-blobs], [iroh-gossip]; build your own with [irpc]

[iroh.computer](https://iroh.computer) · [docs.iroh.computer](https://docs.iroh.computer) · [github.com/n0-computer/iroh](https://github.com/n0-computer/iroh)

[Using QUIC to traverse NATs]: https://datatracker.ietf.org/doc/draft-seemann-quic-nat-traversal/
[approved draft RFC]: https://datatracker.ietf.org/doc/draft-ietf-quic-multipath/
[Media over QUIC]: https://datatracker.ietf.org/wg/moq/about/
[iroh-blobs]: https://docs.rs/iroh-blobs
[iroh-gossip]: https://docs.rs/iroh-gossip
[irpc]: https://docs.rs/irpc
[HTTP/3]: https://www.rfc-editor.org/rfc/rfc9114
[MASQUE]: https://datatracker.ietf.org/wg/masque/about/
