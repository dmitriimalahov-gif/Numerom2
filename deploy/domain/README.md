# NumerOM — https://1.numer.om

Production branch: `codex/numerom-production` in `dmitriimalahov-gif/Numerom2`.
Each push to that branch runs `.github/workflows/numerom-domain.yml`: install locked
frontend dependencies, typecheck and mobile tests, Expo production export, public-file
secret audit, restricted SSH upload, atomic symlink activation and HTTPS/API checks.
Use a reviewed commit containing the intended mobile/package updates; do not publish
private runtime data or model/reference audio. Failed builds retain the current release.

The Ubuntu host serves Nginx HTTPS and `/srv/numerom/current`; browser releases live
under `/srv/numerom/releases`. `/release.json` identifies the deployed source commit.
An upload key is restricted to the root-owned `numerom-release` receiver, with no
shell or forwarding. GitHub secrets `NUMEROM_DEPLOY_SSH_KEY` and
`NUMEROM_DEPLOY_KNOWN_HOSTS` contain its private credential and pinned host keys.

Authoritative API, MongoDB, private media, bots and speech jobs remain in the existing
Mac runtime. A restricted reverse SSH connection forwards server loopback port18804
to Mac gateway8004. `md.numerom.domain-bridge` reconnects automatically; the existing
watchdog uses `NUMEROM_PUBLIC_ORIGIN=https://1.numer.om` and never replaces it with a
Quick Tunnel address. Nginx replaces the trusted peer header with the actual visitor
IP. Backend owner checks, authorization and signed/private media routes are retained.
**Server functions still require the Mac and its Internet connection to be online.**
This deployment does not migrate the database or voice generation to Ubuntu.

For a backend code update deploy reviewed code to the existing authoritative runtime,
run relevant tests and reload only affected services; frontend CI deliberately cannot
read its secrets, modify MongoDB, or restart ongoing narration/rendering.

The receiver records immutable release directories. Roll back by atomically pointing
`/srv/numerom/current` to an earlier verified directory; no Nginx reload is needed.
TLS uses Certbot webroot and its existing auto-renewal timer. Other hosted projects
have separate Nginx configurations and were not changed.
