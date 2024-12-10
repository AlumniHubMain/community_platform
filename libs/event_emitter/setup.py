from setuptools import setup

setup(
    name="alumnihub-event-emitter",
    version="0.1.0",
    description="Notification event emitter for AlumniHub community platform",
    author="Sergey Sedov",
    author_email="sergey.sedov@gmail.com",
    url="https://github.com/AlumniHubMain/community_platform/",
    packages=["alumnihub.community_platform.event_emitter"],
    package_dir={"": "src"},  # Point to the `src` directory
    include_package_data=True,  # Include additional files specified below
    package_data={
        # Specify the package and the files to include
        "alumnihub.community_platform.event_emitter": [
            "generated/*_pb2.py",  # Include all Python files in the generated directory
            "generated/*_pb2.pyi",  # Include all Python files in the generated directory
        ],
    },
    install_requires=[
        "google-cloud-pubsub",
        "protobuf",
        "pydantic",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.12",
        #        "License :: OSI Approved :: MIT License", ToDo: decide on the licence
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
