"""
Lock manager to prevent duplicate bot executions.
Uses file-based locking compatible with GitHub Actions.
"""

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path


class LockManager:
    """Manage execution locks to prevent duplicate runs."""

    def __init__(self, lock_timeout_minutes: int = 60):
        """
        Initialize lock manager.

        Args:
            lock_timeout_minutes: Lock expires after this many minutes
        """
        self.lock_timeout = timedelta(minutes=lock_timeout_minutes)
        # Use temp directory for lock file (works in GitHub Actions)
        self.lock_dir = Path(tempfile.gettempdir())
        self.lock_file = self.lock_dir / "rupiah_emas_bot.lock"

    def acquire_lock(self) -> bool:
        """
        Try to acquire execution lock.

        Returns:
            True if lock acquired, False if another instance is running
        """
        try:
            # Check if lock file exists
            if self.lock_file.exists():
                # Read lock metadata
                lock_data = self.lock_file.read_text().strip()
                if lock_data:
                    lock_time = datetime.fromisoformat(lock_data)
                    age = datetime.now() - lock_time

                    # Check if lock is stale (expired)
                    if age > self.lock_timeout:
                        print(f"Lock file is stale ({age}), removing...")
                        self.lock_file.unlink()
                    else:
                        # Lock is still valid
                        print(f"Lock already held (age: {age}), skipping execution")
                        return False

            # Acquire lock by writing current timestamp
            self.lock_file.write_text(datetime.now().isoformat())
            print(f"Lock acquired: {self.lock_file}")
            return True

        except Exception as e:
            print(f"Error acquiring lock: {e}")
            # Fail open - allow execution if lock mechanism fails
            return True

    def release_lock(self) -> None:
        """Release the execution lock."""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                print("Lock released")
        except Exception as e:
            print(f"Error releasing lock: {e}")

    def __enter__(self):
        """Context manager entry."""
        if not self.acquire_lock():
            raise RuntimeError("Could not acquire lock - another instance is running")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - always release lock."""
        self.release_lock()
        return False  # Don't suppress exceptions
