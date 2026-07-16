# Root Dockerfile intentionally replaced to avoid accidental builds from the repository root.
# Services should use the Dockerfiles inside their folders (backend/Dockerfile, frontend/Dockerfile, scrapers/Dockerfile).
# If you need a root-level Dockerfile later, recreate it intentionally.

FROM scratch
CMD ["/bin/true"]
