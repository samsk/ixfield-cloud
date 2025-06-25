"""Common optimistic state update functionality for IXField components."""
import asyncio
import logging
from typing import Any, Optional, Callable, Awaitable
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

class OptimisticStateManager:
    """Manages optimistic state updates for IXField components."""
    
    def __init__(self, entity_name: str, entity_type: str):
        """Initialize the optimistic state manager."""
        self.entity_name = entity_name
        self.entity_type = entity_type
        self._optimistic_value: Optional[Any] = None
        self._pending_operation = False
        self._entity_ref = None  # Reference to the entity for state updates
    
    def set_entity_ref(self, entity_ref):
        """Set reference to the entity for state updates."""
        self._entity_ref = entity_ref
    
    def get_current_value(self, coordinator_value: Any) -> Any:
        """Get the current value, using optimistic value if available."""
        if self._pending_operation and self._optimistic_value is not None:
            _LOGGER.debug(f"{self.entity_type} {self.entity_name} using optimistic value: {self._optimistic_value}")
            return self._optimistic_value
        
        _LOGGER.debug(f"{self.entity_type} {self.entity_name} using coordinator value: {coordinator_value}")
        return coordinator_value
    
    def is_operation_pending(self) -> bool:
        """Check if an operation is currently pending."""
        return self._pending_operation
    
    async def execute_with_optimistic_update(
        self,
        target_value: Any,
        api_call: Callable[[], Awaitable[bool]],
        verification_call: Callable[[], Any],
        value_comparison: Callable[[Any, Any], bool] = None,
        delay_before_refresh: float = 3.0,
        delay_before_verification: float = 2.0,
        coordinator_refresh: Callable[[], Awaitable[None]] = None,
        entity_state_update: Callable[[], None] = None
    ) -> bool:
        """
        Execute an operation with optimistic state updates.
        
        Args:
            target_value: The target value to set
            api_call: Async function that makes the API call, returns success bool
            verification_call: Function that gets the actual value for verification
            value_comparison: Function to compare expected vs actual values (default: equality)
            delay_before_refresh: Seconds to wait before refreshing coordinator data
            delay_before_verification: Seconds to wait before verifying the state
            coordinator_refresh: Async function to refresh coordinator data
            entity_state_update: Function to force entity state update
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        if self._pending_operation:
            _LOGGER.warning(f"{self.entity_type} {self.entity_name} operation already in progress, ignoring new request")
            return False
        
        _LOGGER.info(f"Setting {self.entity_type} {self.entity_name} to {target_value}")
        
        # Set optimistic value immediately
        self._optimistic_value = target_value
        self._pending_operation = True
        
        # Force immediate UI update if entity reference is available
        if entity_state_update:
            entity_state_update()
        elif self._entity_ref and hasattr(self._entity_ref, 'async_write_ha_state'):
            self._entity_ref.async_write_ha_state()
        
        try:
            # Send the API request
            success = await api_call()
            
            if success:
                _LOGGER.info(f"Successfully sent {target_value} command to {self.entity_name}")
                
                # Wait for cloud state to update
                if delay_before_refresh > 0:
                    await asyncio.sleep(delay_before_refresh)
                
                # Refresh coordinator data
                if coordinator_refresh:
                    await coordinator_refresh()
                
                # Wait a bit more and verify the state
                if delay_before_verification > 0:
                    await asyncio.sleep(delay_before_verification)
                
                # Verify the state change was successful
                actual_value = verification_call()
                
                # Use custom comparison function or default equality
                if value_comparison:
                    is_verified = value_comparison(target_value, actual_value)
                else:
                    is_verified = target_value == actual_value
                
                if is_verified:
                    _LOGGER.info(f"{self.entity_type} {self.entity_name} state change verified successfully")
                else:
                    _LOGGER.warning(f"{self.entity_type} {self.entity_name} state verification failed. Expected: {target_value}, Actual: {actual_value}")
                    # Force another refresh to get the correct state
                    if coordinator_refresh:
                        await coordinator_refresh()
            else:
                _LOGGER.error(f"Failed to send {target_value} command to {self.entity_name}")
                # Revert optimistic value on failure
                self._revert_optimistic_state(entity_state_update)
                
        except Exception as e:
            _LOGGER.error(f"Exception while setting {self.entity_name} to {target_value}: {e}")
            # Revert optimistic value on exception
            self._revert_optimistic_state(entity_state_update)
        finally:
            # Clear pending operation flag
            self._pending_operation = False
            self._optimistic_value = None
        
        return success
    
    def _revert_optimistic_state(self, entity_state_update: Callable[[], None] = None):
        """Revert the optimistic state and update UI."""
        self._optimistic_value = None
        
        # Force UI update to revert the optimistic state
        if entity_state_update:
            entity_state_update()
        elif self._entity_ref and hasattr(self._entity_ref, 'async_write_ha_state'):
            self._entity_ref.async_write_ha_state()

# Common comparison functions
def float_comparison_with_tolerance(expected: float, actual: float, tolerance: float = 0.1) -> bool:
    """Compare float values with tolerance for floating point differences."""
    if actual is None:
        return False
    return abs(actual - expected) < tolerance

def string_comparison_ignore_case(expected: str, actual: str) -> bool:
    """Compare string values ignoring case."""
    if actual is None:
        return False
    return expected.lower() == actual.lower()

def boolean_comparison(expected: bool, actual: Any) -> bool:
    """Compare boolean values, handling various boolean representations."""
    if actual is None:
        return False
    
    # Handle various boolean representations
    if isinstance(actual, bool):
        return expected == actual
    elif isinstance(actual, str):
        return expected == (actual.lower() in ["true", "on", "1", "yes"])
    elif isinstance(actual, (int, float)):
        return expected == (actual != 0)
    
    return False 