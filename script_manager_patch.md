# Script Manager Patch - Caching time_relevance

## Apply Patch

Add to `__init__` of ScriptManager class:

```python
self._time_relevance_cache = {}  # {script_path: (timestamp, value)}
self._cache_ttl = 300  # 5 minutes
```

Replace `_get_time_relevance_bonus` method:

```python
def _get_time_relevance_bonus(self, script: ScriptInfo) -> float:
    """Get time relevance bonus (with caching)"""
    import time as time_module
    
    now = time_module.time()
    if script.path in self._time_relevance_cache:
        cached_time, cached_value = self._time_relevance_cache[script.path]
        if now - cached_time < self._cache_ttl:
            return cached_value
    
    # Calculate (if cache expired)
    # ... old code ...
    
    # Save to cache
    self._time_relevance_cache[script.path] = (now, value)
    return value
```

## Why

Method `_get_time_relevance_bonus` is called for each script on every recommendations update.

With 50 scripts: 50 * (read history + loop through records)

## Effect

- Before: O(n * m) where n = scripts, m = history records
- After: O(1) on cache hit

## When to Apply

- If >50 scripts
- If recommendation updates are frequent
- If noticeable lag when opening widget

## When NOT to Apply

- If <20 scripts
- If no performance issues
