CONFIGS_LOCAL_DIR=""
SECRETS_LOCAL_DIR=""

GATEWAY_IMAGE_NAME="web_gateway-web-gateway-service"
GATEWAY_IMAGE_VERSION="latest"
NETWORK_NAME="web-gateway-testing-network"
DB_CONTAINER_NAME="alumni-test-database"

POSITIONAL_ARGS=()

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --configs)
      CONFIGS_LOCAL_DIR="$2"
      shift
      shift
      ;;
    --secrets)
      SECRETS_LOCAL_DIR="$2"
      shift
      shift
      ;;
    --gateway-image-name)
      GATEWAY_IMAGE_NAME="$2"
      shift
      shift
      ;;
    --gateway-image-version)
      GATEWAY_IMAGE_VERSION="$2"
      shift
      shift
      ;;
    --db-container)
      DB_CONTAINER_NAME="$2"
      shift
      shift
      ;;
    --help)
      echo "Script for running tests of the Web Gateway service."
      echo "Preparation before running:"
      echo "  You need to up docker container with PostgreSQL database before run this script."
      echo "  After it you might"
      echo "The possible options for starting the operation are listed below:"
      echo "> [required] --configs /path/to/configs/dir     - path to directory with configuration files for service."
      echo "> [required] --secrets /path/to/secrets/dir     - path to directory with secret files for service."
      echo "> [optional] --gateway-image-name name_of_image - the name under which the Web Gateway image of the service will be created."
      echo "> [optional] --gateway-image-version version    - the tag under which the Web Gateway image of the service will be created."
      echo "> [optional] --db-container                     - the name of container with database."
      exit 0;;
    -*|--*)
      echo "Unknown option $1"
      exit 1
      ;;
    *)
      POSITIONAL_ARGS+=("$1") # save positional arg
      shift # past argument
      ;;
  esac
done

# Validate required arguments
if [[ ${CONFIGS_LOCAL_DIR} -eq "" ]]; then
    echo "Error. Local directory with service configuration files must be setted by command line arguments."
    echo "See --help for details."
    exit 1
fi

if [[ ${SECRETS_LOCAL_DIR} -eq "" ]]; then
    echo "Error. Local directory with service secret files must be setted by command line arguments."
    echo "See --help for details."
    exit 1
fi

echo "Running script with settings:"
echo "    CONFIGS_LOCAL_DIR=${CONFIGS_LOCAL_DIR}"
echo "    SECRETS_LOCAL_DIR=${SECRETS_LOCAL_DIR}"
echo "    GATEWAY_IMAGE_NAME=${GATEWAY_IMAGE_NAME}"
echo "    GATEWAY_IMAGE_VERSION=${GATEWAY_IMAGE_VERSION}"
echo "    DB_CONTAINER_NAME=${DB_CONTAINER_NAME}"


RUN_TESTS_CMD="uv run pytest"
# Add print cout
RUN_TESTS_CMD="${RUN_TESTS_CMD} -s"

MOUNTS="${MOUNTS} -v ${CONFIGS_LOCAL_DIR}:/config:rw"
MOUNTS="${MOUNTS} -v ${SECRETS_LOCAL_DIR}:/secrets:rw"


# Setup docker images and environment
docker build . --build-context root='../../' -t ${GATEWAY_IMAGE_NAME}:${GATEWAY_IMAGE_VERSION}
if [ $? -eq 1 ]; then
    echo "Failed to build images. See debug info."
    exit 1
fi


# Create network if needed
if docker network ls | grep -q ${NETWORK_NAME}; then
    echo "Network ${NETWORK_NAME} already exists."
else
    docker network create ${NETWORK_NAME}
    if [ $? -eq 1 ]; then
        echo "Failed to create network. See debug info."
        exit 1
    fi
fi


# Add DB container to network
if docker network inspect ${NETWORK_NAME} | grep -q ${DB_CONTAINER_NAME}; then
    echo "Database container ${DB_CONTAINER_NAME} already included into ${NETWORK_NAME} network."
else
    docker network connect ${NETWORK_NAME} ${DB_CONTAINER_NAME}
if [ $? -eq 1 ]; then
    echo "Failed to connect database container to network. See debug info."
    exit 1
fi
fi


# DB Migration
RUN_MIGRATION_CMD="cd /build && /build/apps/web_gateway/.venv/bin/python scripts/setup_db.py"
docker run ${MOUNTS} --network ${NETWORK_NAME} ${GATEWAY_IMAGE_NAME}:${GATEWAY_IMAGE_VERSION} /bin/bash -c "${RUN_MIGRATION_CMD}"
if [ $? -eq 1 ]; then
    echo "Failed to apply migration. See debug info."
    exit 1
fi


# Run tests
docker run -it ${MOUNTS} --network ${NETWORK_NAME} ${GATEWAY_IMAGE_NAME}:${GATEWAY_IMAGE_VERSION} /bin/bash -c "${RUN_TESTS_CMD}"
if [ $? -eq 1 ]; then
    echo "Tests failed."
    exit 1
fi
