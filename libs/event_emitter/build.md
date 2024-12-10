# Commands to build and upload

```shell
python setup.py sdist bdist_wheel

twine upload --repository community-platform dist/*
```

Environment setup taken from https://console.cloud.google.com/artifacts/python/communityp-440714/europe-west3/community-platform?chat=true&inv=1&invt=AbjwaA&project=communityp-440714
