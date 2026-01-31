"""
Enhanced EventBus
Advanced publish-subscribe event system with async support and history
"""
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import threading
import logging
import traceback

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Represents an event with metadata."""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }


class EventBus:
    """
    Enhanced event bus for publish-subscribe pattern.
    
    Features:
    - Synchronous and asynchronous event handling
    - Event history tracking
    - Priority-based event handling
    - Error handling and recovery
    - Event filtering and middleware
    
    Usage:
        bus = EventBus(history_size=100)
        bus.subscribe("user.login", my_handler, priority=1)
        bus.emit("user.login", user_id=123, username="john")
    """
    
    def __init__(self, history_size: int = 0):
        """
        Initialize event bus.
        
        Args:
            history_size: Number of events to keep in history (0 to disable)
        """
        self._subscribers: Dict[str, List[tuple]] = {}  # event_name -> [(priority, callback), ...]
        self._history: Optional[deque] = deque(maxlen=history_size) if history_size > 0 else None
        self._lock = threading.RLock()
        self._middleware: List[Callable[[Event], Optional[Event]]] = []
        self._running = True
    
    def subscribe(
        self,
        event_name: str,
        callback: Callable,
        priority: int = 0
    ) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of the event to subscribe to
            callback: Function to call when event is emitted
            priority: Higher priority callbacks are called first (default 0)
        """
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            
            # Check for duplicate
            for _, existing_callback in self._subscribers[event_name]:
                if existing_callback == callback:
                    logger.warning(f"Callback already subscribed to {event_name}")
                    return
            
            # Add with priority
            self._subscribers[event_name].append((priority, callback))
            # Sort by priority (descending)
            self._subscribers[event_name].sort(key=lambda x: x[0], reverse=True)
            
            logger.debug(f"Subscribed to event: {event_name} (priority={priority})")
    
    def unsubscribe(self, event_name: str, callback: Callable) -> bool:
        """
        Unsubscribe from an event.
        
        Args:
            event_name: Name of the event
            callback: Callback to remove
            
        Returns:
            True if callback was removed
        """
        with self._lock:
            if event_name not in self._subscribers:
                return False
            
            original_len = len(self._subscribers[event_name])
            self._subscribers[event_name] = [
                (p, cb) for p, cb in self._subscribers[event_name]
                if cb != callback
            ]
            
            removed = len(self._subscribers[event_name]) < original_len
            if removed:
                logger.debug(f"Unsubscribed from event: {event_name}")
            
            return removed
    
    def emit(self, event_name: str, source: Optional[str] = None, **kwargs) -> None:
        """
        Emit an event to all subscribers.
        
        Args:
            event_name: Name of the event
            source: Source identifier for the event
            **kwargs: Event data to pass to subscribers
        """
        event = Event(name=event_name, data=kwargs, source=source)
        
        # Apply middleware
        for middleware in self._middleware:
            try:
                event = middleware(event)
                if event is None:
                    return  # Event was filtered out
            except Exception as e:
                logger.error(f"Middleware error for event {event_name}: {e}")
                continue
        
        # Add to history
        if self._history is not None:
            self._history.append(event)
        
        # Get subscribers
        with self._lock:
            subscribers = self._subscribers.get(event_name, [])
        
        if not subscribers:
            return
        
        logger.debug(f"Emitting event: {event_name} to {len(subscribers)} subscribers")
        
        # Call subscribers
        for priority, callback in subscribers:
            try:
                callback(**kwargs)
            except Exception as e:
                logger.error(f"Error in event handler for {event_name}: {e}")
                logger.debug(traceback.format_exc())
    
    def emit_async(
        self,
        event_name: str,
        source: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Emit an event asynchronously (non-blocking).
        
        Args:
            event_name: Name of the event
            source: Source identifier
            **kwargs: Event data
        """
        import threading
        thread = threading.Thread(
            target=self.emit,
            args=(event_name, source),
            kwargs=kwargs,
            daemon=True
        )
        thread.start()
    
    def once(self, event_name: str, callback: Callable, priority: int = 0) -> None:
        """
        Subscribe to an event for one-time execution.
        
        Args:
            event_name: Event name to subscribe to
            callback: Function to call once
            priority: Handler priority
        """
        def one_time_handler(**kwargs):
            self.unsubscribe(event_name, one_time_handler)
            callback(**kwargs)
        
        self.subscribe(event_name, one_time_handler, priority)
    
    def add_middleware(self, middleware: Callable[[Event], Optional[Event]]) -> None:
        """
        Add middleware for event processing.
        
        Args:
            middleware: Function that takes an Event and returns Event or None
        """
        self._middleware.append(middleware)
        logger.debug(f"Added middleware. Total: {len(self._middleware)}")
    
    def remove_middleware(self, middleware: Callable[[Event], Optional[Event]]) -> bool:
        """
        Remove middleware.
        
        Args:
            middleware: Middleware function to remove
            
        Returns:
            True if removed
        """
        if middleware in self._middleware:
            self._middleware.remove(middleware)
            return True
        return False
    
    def get_history(self, event_name: Optional[str] = None, limit: int = 10) -> List[Event]:
        """
        Get event history.
        
        Args:
            event_name: Optional filter by event name
            limit: Maximum number of events to return
            
        Returns:
            List of events (most recent first)
        """
        if self._history is None:
            return []
        
        events = list(self._history)
        
        if event_name:
            events = [e for e in events if e.name == event_name]
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    def clear_history(self) -> None:
        """Clear event history."""
        if self._history is not None:
            self._history.clear()
    
    def clear(self, event_name: str = None) -> None:
        """
        Clear subscribers for an event or all events.
        
        Args:
            event_name: Event to clear, or None to clear all
        """
        with self._lock:
            if event_name:
                if event_name in self._subscribers:
                    del self._subscribers[event_name]
                    logger.debug(f"Cleared subscribers for: {event_name}")
            else:
                self._subscribers.clear()
                logger.debug("Cleared all subscribers")
    
    def get_subscribers(self, event_name: str) -> List[Callable]:
        """
        Get list of subscribers for an event.
        
        Args:
            event_name: Event name
            
        Returns:
            List of callback functions
        """
        with self._lock:
            return [cb for _, cb in self._subscribers.get(event_name, [])]
    
    def has_subscribers(self, event_name: str) -> bool:
        """
        Check if an event has subscribers.
        
        Args:
            event_name: Event name
            
        Returns:
            True if event has subscribers
        """
        with self._lock:
            return event_name in self._subscribers and len(self._subscribers[event_name]) > 0
    
    def shutdown(self) -> None:
        """Shutdown the event bus and clear all resources."""
        self._running = False
        self.clear()
        self.clear_history()
        self._middleware.clear()
        logger.info("EventBus shutdown")


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """Get or create the global event bus instance."""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus(history_size=100)
    return _global_event_bus


def reset_global_event_bus() -> None:
    """Reset the global event bus."""
    global _global_event_bus
    if _global_event_bus is not None:
        _global_event_bus.shutdown()
    _global_event_bus = EventBus(history_size=100)
