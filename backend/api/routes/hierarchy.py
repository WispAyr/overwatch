"""
Hierarchy API route
Returns complete organizational hierarchy
"""
from fastapi import APIRouter

from core.hierarchy import HierarchyLoader


router = APIRouter()


@router.get("/tree")
async def get_hierarchy_tree():
    """Get complete organizational hierarchy tree"""
    loader = HierarchyLoader()
    tree = await loader.get_hierarchy_tree()
    return tree
    

@router.post("/reload")
async def reload_hierarchy():
    """Reload hierarchy from configuration file"""
    loader = HierarchyLoader()
    await loader.load_hierarchy()
    return {"message": "Hierarchy reloaded"}

