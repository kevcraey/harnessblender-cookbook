# jenking-mcp

Eigen wrapper rond de upstream Jenking MCP-server, geen vendored kopie.

- **Origin**: [Breina/Jenking](https://github.com/Breina/Jenking) (Go, GPL-3.0), gepind op release `v1.0.1`.
- **Dependency**: de wrapper installeert zelf de release-binary bij eerste start in
  `~/.local/share/jenking-mcp/<versie>/jenking`, na verificatie van de SHA-256 uit `checksums.txt`.
  Geen `install.sh` van upstream (volgt `latest`, geen checksum). Enkel darwin/arm64 is gepind.
- **Credentials**: macOS Keychain, generic password `jenkins-pat`. Account = Jenkins-username,
  wachtwoord = API-token. De token gaat enkel via env var `JENKINS_TOKEN` naar jenking.
- **Config**: jenking leest hardcoded `~/.config/jenking/config.yaml`. De wrapper maakt die enkel aan
  als ze ontbreekt (context `cumuli`, zonder token); bestaande config blijft onaangeroerd.
- **Modus**: `--read-only` (enkel lees-tools). Weghalen in `jenking-mcp.sh` om builds te kunnen triggeren.
- **Upgraden**: `VERSION` en `SHA256_DARWIN_ARM64` aanpassen in `jenking-mcp.sh`.
- **Nieuwe machine**: keychain-item `jenkins-pat` aanmaken, dan werkt `jenking-mcp.sh` meteen.

`.claude-plugin/.mcp.json` wijst met een absoluut pad naar `jenking-mcp.sh` in deze map —
niet bundelbaar (zie harnessblender-conventie), dus enkel bruikbaar op deze machine.
