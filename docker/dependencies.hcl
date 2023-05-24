group "lock-dependencies" {
  targets = ["updated-poetry-lockfile", "updated-base-image-lockfile"]
}

target "_base" {
  args = { cache_invalidator = timestamp() }
}

target "updated-poetry-lockfile" {
  inherits = ["_base"]
  dockerfile = "dependencies.Dockerfile"
  target = "updated-poetry-lockfile"
  output = ["type=local,dest=locked-versions"]
}

target "updated-base-image-lockfile" {
  inherits = ["_base"]
  dockerfile = "dependencies.Dockerfile"
  target = "updated-base-image-lockfile"
  output = ["type=local,dest=locked-versions"]
}
