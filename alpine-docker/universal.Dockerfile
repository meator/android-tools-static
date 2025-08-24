# Beware! https://docs.docker.com/reference/dockerfile/#understand-how-arg-and-from-interact
ARG ALPINE_VERSION=3.22

FROM alpine:${ALPINE_VERSION}

# Some of these may not be entirely necessary, but better safe than sorry.
RUN apk add --no-cache --virtual .build-deps make patch gcc g++ file perl python3 build-base linux-headers autoconf automake libtool bison rsync

ARG MUSL_CROSS_MAKE_VERSION=4be756d35cb0c603ba9255a9fb187c39e082413b

# ADD https://github.com/richfelker/musl-cross-make/archive/refs/tags/v${MUSL_CROSS_MAKE_VERSION}.tar.gz .
ADD https://github.com/richfelker/musl-cross-make/archive/${MUSL_CROSS_MAKE_VERSION}.tar.gz .

ARG BINUTILS_VERSION=2.44
ARG GCC_VERSION=14.2.0
ARG MUSL_VERSION=1.2.5
ARG GMP_VERSION=6.1.2
ARG MPC_VERSION=1.1.0
ARG MPFR_VERSION=4.0.2
ARG LINUX_VERSION=headers-4.19.88-1
ARG ISL_VERSION=headers-4.19.88-1

RUN cat > config-versions.mak <<EOF
BINUTILS_VER = ${BINUTILS_VERSION}
GCC_VER = ${GCC_VERSION}
MUSL_VER = ${MUSL_VERSION}
GMP_VER = ${GMP_VERSION}
MPC_VER = ${MPC_VERSION}
MPFR_VER = ${MPFR_VERSION}
LINUX_VER = ${LINUX_VERSION}
ISL_VER = ${ISL_VERSION}
EOF

ARG TARGET_MAK_FILE

COPY config-base.mak ${TARGET_MAK_FILE} .

RUN <<EOF
set -e
tar -xf ${MUSL_CROSS_MAKE_VERSION}.tar.gz
cat config-base.mak config-versions.mak ${TARGET_MAK_FILE} > musl-cross-make-${MUSL_CROSS_MAKE_VERSION}/config.mak
make -C musl-cross-make-${MUSL_CROSS_MAKE_VERSION}/ -j$(nproc)
make -C musl-cross-make-${MUSL_CROSS_MAKE_VERSION}/ install
rm -rf musl-cross-make-${MUSL_CROSS_MAKE_VERSION}/
EOF

ARG ALPINE_VERSION
ARG DOCKER_SETUP_BUILDX_ACTION_VERSION
ARG DOCKER_LOGIN_ACTION_VERSION
ARG DOCKER_METADATA_ACTION_VERSION
ARG DOCKER_BAKE_ACTION_VERSION

COPY save-versions.py /

RUN <<EOF
python3 /save-versions.py \
  --alpine-version "${ALPINE_VERSION}" \
  --musl-cross-make-version "${MUSL_CROSS_MAKE_VERSION}" \
  --binutils-version "${BINUTILS_VERSION}" \
  --gcc-version "${GCC_VERSION}" \
  --musl-version "${MUSL_VERSION}" \
  --gmp-version "${GMP_VERSION}" \
  --mpc-version "${MPC_VERSION}" \
  --mpfr-version "${MPFR_VERSION}" \
  --linux-version "${LINUX_VERSION}" \
  --isl-version "${ISL_VERSION}" \
  --setup-buildx-action-version "${DOCKER_SETUP_BUILDX_ACTION_VERSION}" \
  --login-action-version "${DOCKER_LOGIN_ACTION_VERSION}" \
  --metadata-action-version "${DOCKER_METADATA_ACTION_VERSION}" \
  --bake-action-version "${DOCKER_BAKE_ACTION_VERSION}" \
  > /version-info.json || exit 1
EOF

RUN <<EOF
set -e
apk del .build-deps
rm -rf .build-deps ${MUSL_CROSS_MAKE_VERSION}.tar.gz config-versions.mak config-base.mak save-versions.py ${TARGET_MAK_FILE}
EOF

LABEL "reproducibility.versions.alpine"="${ALPINE_VERSION}"
LABEL "reproducibility.versions.musl-cross-make"="${MUSL_CROSS_MAKE_VERSION}"
LABEL "reproducibility.versions.binutils"="${BINUTILS_VERSION}"
LABEL "reproducibility.versions.gcc"="${GCC_VERSION}"
LABEL "reproducibility.versions.musl"="${MUSL_VERSION}"
LABEL "reproducibility.versions.gmp"="${GMP_VERSION}"
LABEL "reproducibility.versions.mpc"="${MPC_VERSION}"
LABEL "reproducibility.versions.mpfr"="${MPFR_VERSION}"
LABEL "reproducibility.versions.linux"="${LINUX_VERSION}"
LABEL "reproducibility.versions.docker/setup-buildx-action"="${DOCKER_SETUP_BUILDX_ACTION_VERSION}"
LABEL "reproducibility.versions.docker/login-action"="${DOCKER_LOGIN_ACTION_VERSION}"
LABEL "reproducibility.versions.docker/metadata-action"="${DOCKER_METADATA_ACTION_VERSION}"
LABEL "reproducibility.versions.docker/bake-action"="${DOCKER_BAKE_ACTION_VERSION}"
