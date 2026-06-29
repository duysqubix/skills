# Test harness for install.sh — this is NOT a skill (no SKILL.md), so the installer ignores it.
#
# Build == test:
#   docker build -t skills-install-test .
#
# It seeds an UNRELATED pre-existing skill, runs the installer against the public
# mirror, then asserts the contract: the library's skills land, the unrelated skill
# survives untouched, and repo-meta files are NOT copied. A failed assertion fails
# the build.
FROM debian:stable-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates tar \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /test
COPY install.sh .

# Seed an UNRELATED skill that MUST survive untouched (the no-clobber contract):
RUN mkdir -p /root/.agents/skills/my-existing-skill \
 && printf 'SENTINEL-DO-NOT-CLOBBER\n' > /root/.agents/skills/my-existing-skill/SKILL.md

# Run the installer, then assert the full contract:
RUN sh install.sh \
 && echo "--- asserting install contract ---" \
 && test -f /root/.agents/skills/using-beads/SKILL.md \
 && test -f /root/.agents/skills/using-agent-skills/SKILL.md \
 && test -d /root/.agents/skills/frontend-ui-engineering \
 && grep -q 'SENTINEL-DO-NOT-CLOBBER' /root/.agents/skills/my-existing-skill/SKILL.md \
 && test ! -e /root/.agents/skills/README.md \
 && test ! -e /root/.agents/skills/install.sh \
 && test ! -e /root/.agents/skills/.gitignore \
 && echo "INSTALL TEST PASSED: library skills installed, unrelated skill preserved, repo-meta excluded"
