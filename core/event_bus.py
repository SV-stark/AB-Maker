"""
EventBus: Publish-Subscribe Event System
Enables decoupled communication between components
"""
from typing import Callable, Dict, List
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    Simple event bus for publish-subscribe pattern.
    
    Usage:
        bus = EventBus()
        bus.subscribe("log_message", my_handler)
        bus.emit("log_message", msg="Hello", level="info")
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_name: str, callback: Callable) -> None:
        """
        Subscribe to an event.
        
        Args:
            event_name: Name of the event to subscribe to
            callback: Function to call when event is emitted
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)
            logger.debug(f"Subscribed to event: {event_name}")
    
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """
        Unsubscribe from an event.
        
        Args:
            event_name: Name of the event
            callback: Callback to remove
        """
        if event_name in self._subscribers:
            if callback in self._subscribers[event_name]:
                self._subscribers[event_name].remove(callback)
                logger.debug(f"Unsubscribed from event: {event_name}")
    
    def emit(self, event_name: str, **kwargs) -> None:
        """
        Emit an event to all subscribers.
        
        Args:
            event_name: Name of the event
            **kwargs: Event data to pass to subscribers
        """
        if event_name in self._subscribers:
            logger.debug(f"Emitting event: {event_name} with {len(self._subscribers[event_name])} subscribers")
            for callback in self._subscribers[event_name]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_name}: {e}")
    
    def clear(self, event_name: str = None) -> None:
        """
        Clear subscribers for an event or all events.
        
        Args:
            event_name: Event to clear, or None to clear all
        """
        if event_name:
            if event_name in self._subscribers:
                del self._subscribers[event_name]
        else:
            self._subscribers.clear()
