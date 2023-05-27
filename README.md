# mythril multi-arch container images

This repo provides unofficial arm64 and amd64 container images for
[ConsenSys/mythril](ConsenSys/mythril).

The build uses cross-compilation to create the arm64 image from an amd64
builder, which allows the build to run in GitHub Actions (which doesn't provide
arm64 runners). The container images are signed using
[Cosign](https://www.sigstore.dev/), which makes makes it possible to verify
that a published image was built in a GitHub Action run from this repo. (And
thus you can be sure of its content without building it from source yourself.)

This repo automatically publishes images for new mythril releases and dependency
updates.

## Use the image

Run the image like the myth CLI:

```console
$ docker container run --rm ghcr.io/h4l/mythril/myth version
Mythril version v0.23.22

$ docker container run --rm -v (pwd)/solidity_examples:/solidity_examples \
  ghcr.io/h4l/mythril/myth version analyze /solidity_examples/token.sol
==== Exception State ====
SWC ID: 110
...
```

Or enter an interactive shell:

```console
$ docker container run --rm -v $(pwd)/solidity_examples:/solidity_examples -it \
  ghcr.io/h4l/mythril/myth bash

mythril@6a5e1c3e9871:~$ cd /solidity_examples/

mythril@6a5e1c3e9871:/solidity_examples$ ls
BECToken.sol       etherstore.sol    killbilly.sol    rubixi.sol    token.sol
WalletLibrary.sol  exceptions.sol    origin.sol       suicide.sol   weak_random.sol
calls.sol          hashforether.sol  returnvalue.sol  timelock.sol

mythril@6a5e1c3e9871:/solidity_examples$ myth analyze exceptions.sol
==== Exception State ====
SWC ID: 110
...
```

### Image Configuration

The `SOLC_VERSION` envar controls which versions of solc are available to myth.
It can contain whitespace-separated solc versions:

```
$ docker container run --rm --env "SOLC_VERSION=0.7.6 0.8.15" \
  ghcr.io/h4l/mythril/myth ...
```

Solc binaries are installed via [svm](https://github.com/ethers-rs/svm-rs) on
startup. To avoid re-downloading them, you can mount a volume at
`/home/mythril/.svm` to share solc binaries between containers.

```console
$ docker container run --rm -v solc:/home/mythril/.svm \
  ghcr.io/h4l/mythril/myth svm list
0.7.6 (current)

Installed Versions
0.7.6
0.8.15
0.8.20
...
```

## Verify the provenance of an image

Images published by this repo are signed using cosign, which lets you verify
that an image was built by a GitHub Actions CI run from this repository:

```console
$ docker container run --rm gcr.io/projectsigstore/cosign \
  verify ghcr.io/h4l/mythril/myth@sha256:9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity 'https://github.com/h4l/mythril/.github/workflows/publish-images.yml@refs/heads/main'

Verification for ghcr.io/h4l/mythril/myth@sha256:9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The code-signing certificate was verified using trusted certificate authority certificates

[{"critical":{"identity":{"docker-reference":"ghcr.io/h4l/mythril/myth"},"image":{"docker-manifest-digest":"sha256:9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a"},"type": ...
```

See [Verify the content of an image](#verify-the-content-of-an-image) for more.

## Discover image tags

Discover images using
[`crane ls`](https://github.com/google/go-containerregistry/tree/main/cmd/crane),
or browse the
[repo's registry page](https://githubb.com/h4l/mythril/pkgs/container/mythril-dev%2Fmyth):

```console
$ docker run --rm gcr.io/go-containerregistry/crane \
  ls --full-ref ghcr.io/h4l/mythril/myth | grep -P ':\d+\.\d+\.\d+$'
ghcr.io/h4l/mythril/myth:0.23.22
```

## Get the sha256 digest of a tag

```console
$ docker run --rm gcr.io/go-containerregistry/crane \
  digest ghcr.io/h4l/mythril/myth:0.23.22
sha256:9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a
```

## Pin an exact image version as a short tag

```console
$ docker image pull ghcr.io/h4l/mythril/myth@sha256:9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a
...

$ docker image tag ghcr.io/h4l/mythril/myth@sha256:9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a myth
```

Check the tagged image version:

```console
$ docker image inspect myth --format '{{ .RepoDigests }}'
[ghcr.io/h4l/mythril/myth@sha256:9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a]
```

## Verify the content of an image

Having [verified the provenance of image](#verify-the-provenance-of-an-image)
you can verify the content of the image:

1. Inspect the image-signing certificate's metadata to find the CI run that
   built the image, and verify that the build ran on a GitHub-hosted runner.
2. Check the CI logs to confirm the sha256 digest matches your image
3. Check the state of the git repository at the commit that the CI run ran from

At this point, your remaining trust assumptions should be that GitHub's Actions
runners are secure, and that the dependencies used to build the image are
secure.

Resolve the location of the cosign signature in the container registry:

```console
$ docker container run --rm gcr.io/projectsigstore/cosign triangulate \
  ghcr.io/h4l/mythril/myth@sha256:9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a
ghcr.io/h4l/mythril/myth:sha256-9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a.sig
```

Fetch and print the temporary certificate that was issued to the CI job to sign
the release image. The claims in the certificate are
[derived from the OIDC token GitHub issues to CI jobs](https://docs.sigstore.dev/cosign/openid_signing/):

```console
$ docker run --rm gcr.io/go-containerregistry/crane manifest \
  ghcr.io/h4l/mythril/myth:sha256-9a2f8c8ec45cc496f54333506977a8155b6bc28c83ea028aa5b893bf4714a07a.sig \
  | jq -er '.layers[0].annotations["dev.sigstore.cosign/certificate"]' \
  | openssl x509 -noout -text
```

<details>
  <summary>
    Full Certificate
  </summary>

    Certificate:
        Data:
            Version: 3 (0x2)
            Serial Number:
                2b:24:68:9f:2e:fe:ab:aa:b0:a0:b4:87:a4:54:61:d7:f2:95:36:57
        Signature Algorithm: ecdsa-with-SHA384
            Issuer: O=sigstore.dev, CN=sigstore-intermediate
            Validity
                Not Before: May 27 13:14:52 2023 GMT
                Not After : May 27 13:24:52 2023 GMT
            Subject:
            Subject Public Key Info:
                Public Key Algorithm: id-ecPublicKey
                    Public-Key: (256 bit)
                    pub:
                        04:11:92:4a:8b:a6:39:9a:74:bf:24:25:73:67:6a:
                        a1:9f:92:66:f4:27:85:c7:ca:e1:cd:60:51:b3:e4:
                        be:8e:d1:c0:3e:01:ea:d1:48:8d:2b:45:97:57:97:
                        8f:0f:3c:0c:91:84:44:84:98:b2:3c:f3:4e:e7:3d:
                        a0:f6:f9:dd:29
                    ASN1 OID: prime256v1
                    NIST CURVE: P-256
            X509v3 extensions:
                X509v3 Key Usage: critical
                    Digital Signature
                X509v3 Extended Key Usage:
                    Code Signing
                X509v3 Subject Key Identifier:
                    C7:11:44:2B:4B:EB:62:89:76:D6:4F:25:6B:CA:11:87:5F:4A:13:B5
                X509v3 Authority Key Identifier:
                    keyid:DF:D3:E9:CF:56:24:11:96:F9:A8:D8:E9:28:55:A2:C6:2E:18:64:3F

                X509v3 Subject Alternative Name: critical
                    URI:https://github.com/h4l/mythril/.github/workflows/publish-images.yml@refs/heads/main
                1.3.6.1.4.1.57264.1.1:
                    https://token.actions.githubusercontent.com
                1.3.6.1.4.1.57264.1.2:
                    push
                1.3.6.1.4.1.57264.1.3:
                    e966d5849fd9aa85d9ee77e26ac317b0866595b9
                1.3.6.1.4.1.57264.1.4:
                    Publish Mythril Container Images for linux/amd64 and linux/arm64
                1.3.6.1.4.1.57264.1.5:
                    h4l/mythril
                1.3.6.1.4.1.57264.1.6:
                    refs/heads/main
                1.3.6.1.4.1.57264.1.8:
                    .+https://token.actions.githubusercontent.com
                1.3.6.1.4.1.57264.1.9:
                    .Shttps://github.com/h4l/mythril/.github/workflows/publish-images.yml@refs/heads/main
                1.3.6.1.4.1.57264.1.10:
                    .(e966d5849fd9aa85d9ee77e26ac317b0866595b9
                1.3.6.1.4.1.57264.1.11:
    github-hosted   .
                1.3.6.1.4.1.57264.1.12:
                    ..https://github.com/h4l/mythril
                1.3.6.1.4.1.57264.1.13:
                    .(e966d5849fd9aa85d9ee77e26ac317b0866595b9
                1.3.6.1.4.1.57264.1.14:
                    ..refs/heads/main
                1.3.6.1.4.1.57264.1.15:
                    ..638850745
                1.3.6.1.4.1.57264.1.16:
                    ..https://github.com/h4l
                1.3.6.1.4.1.57264.1.17:
                    ..146503
                1.3.6.1.4.1.57264.1.18:
                    .Shttps://github.com/h4l/mythril/.github/workflows/publish-images.yml@refs/heads/main
                1.3.6.1.4.1.57264.1.19:
                    .(e966d5849fd9aa85d9ee77e26ac317b0866595b9
                1.3.6.1.4.1.57264.1.20:
                    ..push
                1.3.6.1.4.1.57264.1.21:
                    .Ahttps://github.com/h4l/mythril/actions/runs/5098813464/attempts/1
                1.3.6.1.4.1.11129.2.4.2:
                    .{.y.w..=0j...2c....g7..J^..<....r./)......]X.......H0F.!..<.......7c..`.......=G.!...U'.{.!..b..*.%z....*..:]..I....$...bD3.
        Signature Algorithm: ecdsa-with-SHA384
            30:65:02:30:23:a6:1e:41:b7:84:51:7f:25:bc:ce:30:38:75:
            53:f0:6f:f0:d3:dc:f3:04:97:47:bd:e6:eb:80:e9:96:b9:1c:
            1a:65:cd:6f:cc:49:5a:1b:97:b6:10:01:3e:a1:86:ee:02:31:
            00:e2:86:96:09:61:81:a4:e8:96:ae:bf:ce:aa:2d:d6:b0:da:
            86:20:47:8f:17:7a:6a:5c:50:d9:06:d5:3f:07:cc:d0:67:63:
            e2:18:79:31:51:0c:b6:2f:0e:f3:dd:6b:bb

</details>

The certificate contains several X509v3
[fulcio extension attributes](https://github.com/sigstore/fulcio/blob/main/docs/oid-info.md),
such as:

- `1.3.6.1.4.1.57264.1.10` — Build Signer Digest

  ```
              1.3.6.1.4.1.57264.1.10:
                  .(e966d5849fd9aa85d9ee77e26ac317b0866595b9
  ```

- `1.3.6.1.4.1.57264.1.11` — Runner Environment
  ```
              1.3.6.1.4.1.57264.1.11:
  github-hosted   .
  ```
- `1.3.6.1.4.1.57264.1.21` — Run Invocation URI
  ```
              1.3.6.1.4.1.57264.1.21:
                  .Ahttps://github.com/h4l/mythril/actions/runs/5098813464/attempts/1
  ```

(The openssl output is formatted strangely because it doesn't know about the
extension attributes.)

From here you can view the CI logs that built this image and view the git repo's
code at the commit sha that it built at.
