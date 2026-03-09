APEXIS_ROOT=$(find ~/ -type d -name "apexis" -not -path "*/apexis-app/*" -print -quit)
APEXIS_APP="$APEXIS_ROOT/apexis-app"

explanation_script() {
	echo -e "\nUsage: ./test_build.sh [build|test|pipeline|backend]"
    	echo "  build    — create APK"
    	echo "  test     — start Expo for app testing"
    	echo "  pipeline — run index.py locally"
    	echo "  backend  — start FastAPI locally"
}

build_apexis() {
        cd "$APEXIS_APP" &&
        eas build --platform android --profile preview
}

test_apexis() {
        cd "$APEXIS_APP" &&
        npx expo start
}

run_pipeline() {
	cd "$APEXIS_ROOT" &&
	source "/home/betomate/venv/bin/activate" &&
	python index.py
}

run_backend() {
	cd "$APEXIS_ROOT" &&
	source "/home/betomate/venv/bin/activate" &&
	uvicorn backend.main:app --reload
}

if [[ -z "$1" ]]; then
	echo "Need to specify a parameter."
	explanation_script
elif [[ "$1" == "build" ]]; then
	build_apexis
elif [[ "$1" == "test" ]]; then
	test_apexis
elif [[ "$1" == "pipeline" ]]; then
	run_pipeline
elif [[ "$1" == "backend" ]]; then
	run_backend
else
	echo "Unknown option: $1"
	explanation_script
fi
