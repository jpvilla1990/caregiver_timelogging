REGISTRY="harbor.hatarakiassistant.com"
NAMESPACE="docker"

CAREGIVER_IMAGE_NAME="caregiver"

CAREGIVER_TAG="0.6.0"

CAREGIVER_FULL_IMAGE_NAME="${REGISTRY}/${NAMESPACE}/${CAREGIVER_IMAGE_NAME}:${CAREGIVER_TAG}"

if docker pull "${CAREGIVER_FULL_IMAGE_NAME}" > /dev/null 2>&1; then
    echo "Image ${CAREGIVER_FULL_IMAGE_NAME} already exists, skipping build"
else
    docker build -t "${CAREGIVER_FULL_IMAGE_NAME}" -f dockerfile.caregiver .
    docker push "${CAREGIVER_FULL_IMAGE_NAME}"
fi