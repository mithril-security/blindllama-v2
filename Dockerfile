FROM scratch

# Copy SHA256SUMS of input and output artifacts

COPY output/inputs/. inputs/
COPY output/SHA256SUMS SHA256SUMS
