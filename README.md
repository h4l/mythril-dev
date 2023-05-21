# mythril multi-arch container images

This repo provides verifiable arm64 and amd64 container images for
[ConsenSys/mythril](ConsenSys/mythril). (The official images are amd64 only.)

The build uses cross-compilation to create the arm64 image from an amd64
builder, which allows the build to run in GitHub Actions (which doesn't provide
arm64 runners). The container images are signed using Cosign, which makes makes
it possible to verify that an image was created in a GitHub Action run from this
repo.
