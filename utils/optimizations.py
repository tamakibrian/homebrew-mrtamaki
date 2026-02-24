"""
Optimization utilities for CLI tools and interactive menus.
"""
import functools
import time
from typing import Any, Callable, Dict, Optional
import threading

# 1. Lazy loading decorator
class LazyImport:
    """Lazy import module to reduce startup time."""
    
    def __init__(self, module_name: str):
        self.module_name = module_name
        self._module = None
    
    def __getattr__(self, name: str) -> Any:
        if self._module is None:
            self._module = __import__(self.module_name)
        return getattr(self._module, name)

# 2. Caching decorator with TTL (Time To Live)
class TTLCache:
    """Simple TTL cache for expensive operations."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self._cache: Dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                timestamp, value = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
                else:
                    del self._cache[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._cache[key] = (time.time(), value)
    
    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

def cache_with_ttl(ttl_seconds: int = 300):
    """Decorator to cache function results with TTL."""
    cache = TTLCache(ttl_seconds)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key_parts = [func.__name__] + [str(arg) for arg in args]
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        return wrapper
    return decorator

# 3. Connection pooling example (for HTTP requests)
# Note: In practice, use requests.Session() or aiohttp.ClientSession
class ConnectionPool:
    """Simple connection pool for network operations."""
    
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._connections = []
        self._lock = threading.Lock()
    
    def get_connection(self):
        """Get a connection from pool or create new one."""
        with self._lock:
            if self._connections:
                return self._connections.pop()
            # In real implementation, create actual connection
            # For demo, return a placeholder
            return {"id": len(self._connections), "active": True}
    
    def return_connection(self, conn):
        """Return connection to pool."""
        with self._lock:
            if len(self._connections) < self.max_connections:
                self._connections.append(conn)
            else:
                # Close connection if pool is full
                pass

# 4. Generator-based file processing for memory efficiency
def process_large_file(filepath: str, chunk_size: int = 8192):
    """
    Process large files in chunks to reduce memory usage.
    
    Args:
        filepath: Path to the file to process
        chunk_size: Size of each chunk in bytes
    
    Yields:
        Chunks of file data
    """
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

# 5. Menu optimization base class
class OptimizedMenu:
    """
    Base class for optimized interactive menus.
    Implements common patterns to reduce code duplication.
    """
    
    def __init__(self, title: str):
        self.title = title
        self._options = []
        self._cache = TTLCache(ttl_seconds=60)
    
    def add_option(self, name: str, handler: Callable):
        """Add menu option with lazy evaluation support."""
        self._options.append((name, handler))
    
    def display(self):
        """Display menu with cached rendering."""
        cache_key = f"menu_display:{self.title}"
        cached_display = self._cache.get(cache_key)
        
        if cached_display:
            print(cached_display)
        else:
            display_text = self._generate_display()
            self._cache.set(cache_key, display_text)
            print(display_text)
    
    def _generate_display(self) -> str:
        """Generate menu display text."""
        lines = [f"\n=== {self.title} ===", ""]
        for i, (name, _) in enumerate(self._options, 1):
            lines.append(f"{i}. {name}")
        lines.extend(["", "Enter your choice (q to quit): "])
        return "\n".join(lines)
    
    def run(self):
        """Run menu with optimized input handling."""
        while True:
            self.display()
            choice = input().strip().lower()
            
            if choice == 'q':
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(self._options):
                    _, handler = self._options[idx]
                    # Use lazy evaluation for handler if it's a string
                    if isinstance(handler, str):
                        # Import module only when needed
                        module_name, func_name = handler.rsplit('.', 1)
                        module = __import__(module_name, fromlist=[func_name])
                        handler = getattr(module, func_name)
                    handler()
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number or 'q' to quit.")

# Example usage decorator
@cache_with_ttl(ttl_seconds=60)
def expensive_operation(data: str) -> str:
    """Simulate an expensive operation that benefits from caching."""
    time.sleep(2)  # Simulate slow operation
    return f"processed_{data}"

# Memory efficient data processing
def filter_large_dataset(filepath: str, filter_func: Callable):
    """
    Process large datasets without loading everything into memory.
    
    Args:
        filepath: Path to the dataset file
        filter_func: Function to filter each line
    
    Yields:
        Filtered items one at a time
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if filter_func(line.strip()):
                yield line.strip()
