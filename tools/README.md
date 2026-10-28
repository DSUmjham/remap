# tools/

`hello.py` is copied into `workspace/tools/` by `setup.sh`. It proves the stack works before
you write anything. Each `.py` file in `workspace/tools/` becomes one tool server at
`http://localhost:8001/<file name>` (Swagger docs at `/docs`). Files starting with `_` are
helpers and are not served. The name `pyghidra` is reserved.
