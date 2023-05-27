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
  ghcr.io/h4l/mythril-dev/myth:0.23.22 ...
```

Solc binaries are installed via [svm](https://github.com/ethers-rs/svm-rs) on
startup. To avoid re-downloading them, you can mount a volume at
`/home/mythril/.svm` to share solc binaries between containers.

```console
$ docker container run --rm -v solc:/home/mythril/.svm \
  ghcr.io/h4l/mythril-dev/myth:0.23.22 svm list
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
  verify ghcr.io/h4l/mythril-dev/myth@sha256:fe7c14c84f641726c525ca0a5ec8e47237a102117444672843024cea07873dce \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity 'https://github.com/h4l/mythril-dev/.github/workflows/publish-images.yml@refs/heads/main'

Verification for ghcr.io/h4l/mythril-dev/myth@sha256:fe7c14c84f641726c525ca0a5ec8e47237a102117444672843024cea07873dce --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The code-signing certificate was verified using trusted certificate authority certificates

[{"critical":{"identity":{"docker-reference":"ghcr.io/h4l/mythril-dev/myth"},"image":{"docker-manifest-digest":"sha256:fe7c14c84f641726c525ca0a5ec8e47237a102117444672843024cea07873dce"},"type":...
```

See [Verify the content of an image](#verify-the-content-of-an-image) for more.

## Discover image tags

Discover images using
[`crane ls`](https://github.com/google/go-containerregistry/tree/main/cmd/crane),
or browse the
[repo's registry page](https://githubb.com/h4l/mythril-dev/pkgs/container/mythril-dev%2Fmyth):

```console
$ docker run --rm gcr.io/go-containerregistry/crane \
  ls --full-ref ghcr.io/h4l/mythril-dev/myth | grep -P ':\d+\.\d+\.\d+$'
ghcr.io/h4l/mythril-dev/myth:0.23.20
ghcr.io/h4l/mythril-dev/myth:0.23.22
```

## Get the sha256 digest of a tag

```console
$ docker run --rm gcr.io/go-containerregistry/crane \
  digest ghcr.io/h4l/mythril-dev/myth:0.23.22
sha256:fe7c14c84f641726c525ca0a5ec8e47237a102117444672843024cea07873dce
```

## Pin an exact image version as a short tag

```console
$ docker image pull ghcr.io/h4l/mythril-dev/myth:0.23
...

$ docker image tag ghcr.io/h4l/mythril-dev/myth:0.23.22@sha256:fe7c14c84f641726c525ca0a5ec8e47237a102117444672843024cea07873dce myth
```

Check the tagged image version:

```console
$ docker image inspect myth --format '{{ .RepoDigests }}'
[ghcr.io/h4l/mythril-dev/myth@sha256:fe7c14c84f641726c525ca0a5ec8e47237a102117444672843024cea07873dce]
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
  ghcr.io/h4l/mythril-dev/myth@sha256:fe7c14c84f641726c525ca0a5ec8e47237a102117444672843024cea07873dce
ghcr.io/h4l/mythril-dev/myth:sha256-fe7c14c84f641726c525ca0a5ec8e47237a102117444672843024cea07873dce.sig
```

Fetch and print the temporary certificate that was issued to the CI job to sign
the release image. The claims in the certificate are
[derived from the OIDC token GitHub issues to CI jobs](https://docs.sigstore.dev/cosign/openid_signing/):

```console
$ docker run --rm gcr.io/go-containerregistry/crane manifest \
  ghcr.io/h4l/mythril-dev/myth:sha256-fe7c14c84f641726c525ca0a5ec8e47237a102117444672843024cea07873dce.sig \
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
                54:87:a8:03:de:0f:1f:f1:97:66:98:2d:be:96:31:0b:7a:1d:cc:52
        Signature Algorithm: ecdsa-with-SHA384
            Issuer: O=sigstore.dev, CN=sigstore-intermediate
            Validity
                Not Before: May 26 13:46:42 2023 GMT
                Not After : May 26 13:56:42 2023 GMT
            Subject:
            Subject Public Key Info:
                Public Key Algorithm: id-ecPublicKey
                    Public-Key: (256 bit)
                    pub:
                        04:59:d6:3a:44:61:38:e3:5a:12:a9:83:f7:26:02:
                        b3:f1:5d:15:2a:4e:2c:aa:89:03:f9:7f:9a:30:f4:
                        2e:88:ac:4c:bb:e0:ea:ef:62:7e:28:14:6e:04:35:
                        7e:8c:a1:d2:c5:ce:bf:87:81:0f:bf:c1:fe:93:1f:
                        80:f0:ad:e1:51
                    ASN1 OID: prime256v1
                    NIST CURVE: P-256
            X509v3 extensions:
                X509v3 Key Usage: critical
                    Digital Signature
                X509v3 Extended Key Usage:
                    Code Signing
                X509v3 Subject Key Identifier:
                    4F:7C:74:4E:29:2F:40:E0:99:90:05:1B:BA:4D:70:06:D0:2E:1F:9F
                X509v3 Authority Key Identifier:
                    keyid:DF:D3:E9:CF:56:24:11:96:F9:A8:D8:E9:28:55:A2:C6:2E:18:64:3F

                X509v3 Subject Alternative Name: critical
                    URI:https://github.com/h4l/mythril-dev/.github/workflows/publish-images.yml@refs/heads/main
                1.3.6.1.4.1.57264.1.1:
                    https://token.actions.githubusercontent.com
                1.3.6.1.4.1.57264.1.2:
                    push
                1.3.6.1.4.1.57264.1.3:
                    40e4e7771aada4f7b9c324cd8be3621d0f6ce8b6
                1.3.6.1.4.1.57264.1.4:
                    Publish Mythril Container Images for linux/amd64 and linux/arm64
                1.3.6.1.4.1.57264.1.5:
                    h4l/mythril-dev
                1.3.6.1.4.1.57264.1.6:
                    refs/heads/main
                1.3.6.1.4.1.57264.1.8:
                    .+https://token.actions.githubusercontent.com
                1.3.6.1.4.1.57264.1.9:
                    .Whttps://github.com/h4l/mythril-dev/.github/workflows/publish-images.yml@refs/heads/main
                1.3.6.1.4.1.57264.1.10:
                    .(40e4e7771aada4f7b9c324cd8be3621d0f6ce8b6
                1.3.6.1.4.1.57264.1.11:
    github-hosted   .
                1.3.6.1.4.1.57264.1.12:
                    .&quot;https://github.com/h4l/mythril-dev
                1.3.6.1.4.1.57264.1.13:
                    .(40e4e7771aada4f7b9c324cd8be3621d0f6ce8b6
                1.3.6.1.4.1.57264.1.14:
                    ..refs/heads/main
                1.3.6.1.4.1.57264.1.15:
                    ..644238919
                1.3.6.1.4.1.57264.1.16:
                    ..https://github.com/h4l
                1.3.6.1.4.1.57264.1.17:
                    ..146503
                1.3.6.1.4.1.57264.1.18:
                    .Whttps://github.com/h4l/mythril-dev/.github/workflows/publish-images.yml@refs/heads/main
                1.3.6.1.4.1.57264.1.19:
                    .(40e4e7771aada4f7b9c324cd8be3621d0f6ce8b6
                1.3.6.1.4.1.57264.1.20:
                    ..push
                1.3.6.1.4.1.57264.1.21:
                    .Ehttps://github.com/h4l/mythril-dev/actions/runs/5091142381/attempts/1
                1.3.6.1.4.1.11129.2.4.2:
    .2...._.!.....}Q...?g /.1...y....47Y.vK.....&lt;....r./)......XO.......H0F.!...q..^..\..2um..5.UWj...
        Signature Algorithm: ecdsa-with-SHA384
            30:64:02:30:5b:17:32:85:29:06:2a:79:86:15:94:89:f1:73:
            a4:73:7d:42:05:ce:9f:29:84:52:09:19:77:ac:aa:53:98:67:
            ac:b7:54:17:1a:7b:2a:f6:51:e1:09:cc:fb:3a:b2:94:02:30:
            41:41:5a:06:23:fc:23:da:c1:7e:69:1b:5c:17:24:bf:27:4d:
            54:a3:50:91:45:b5:6b:1f:f5:72:3a:4b:f2:05:e1:ea:bd:6e:
            3e:70:8d:b4:ab:be:e3:e3:26:26:d4:33

</details>

The certificate contains several X509v3
[fulcio extension attributes](https://github.com/sigstore/fulcio/blob/main/docs/oid-info.md),
such as:

- `1.3.6.1.4.1.57264.1.11` — Runner Environment
  ```
              1.3.6.1.4.1.57264.1.11:
  github-hosted   .
  ```
- `1.3.6.1.4.1.57264.1.10` — Build Signer Digest

  ```
              1.3.6.1.4.1.57264.1.10:
                  .(40e4e7771aada4f7b9c324cd8be3621d0f6ce8b6
  ```

- `1.3.6.1.4.1.57264.1.21` — Run Invocation URI
  ```
              1.3.6.1.4.1.57264.1.21:
                  .Ehttps://github.com/h4l/mythril-dev/actions/runs/5091142381/attempts/1
  ```

(The openssl output is formatted strangely because it doesn't know about the
extension attributes.)

From here you can view the CI logs that built this image and view the git repo's
code at the commit sha that it built at.
