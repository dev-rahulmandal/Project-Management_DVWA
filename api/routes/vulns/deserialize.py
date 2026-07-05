import base64
import io
import pickle

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...auth import require_auth
from ...hardening import hardened

router = APIRouter()


class ImportRequest(BaseModel):
    data: str


_SAFE_GLOBALS = {
    ("builtins", "dict"), ("builtins", "list"), ("builtins", "tuple"),
    ("builtins", "set"), ("builtins", "str"), ("builtins", "int"),
    ("builtins", "float"), ("builtins", "bool"),
}


class _RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) in _SAFE_GLOBALS:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"blocked global: {module}.{name}")


@router.post("/api/preferences/import")
async def import_prefs(request: Request, body: ImportRequest, user: dict = Depends(require_auth)):
    if hardened(request):
        try:
            obj = _RestrictedUnpickler(io.BytesIO(base64.b64decode(body.data))).load()
        except pickle.UnpicklingError:
            raise HTTPException(status_code=400, detail="blocked")
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"import_error: {exc}")
        return {"imported": True, "value": str(obj)[:200]}
    try:
        obj = pickle.loads(base64.b64decode(body.data))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"import_error: {exc}")
    return {"imported": True, "value": str(obj)[:200]}
