"""
Rate limiting module for Foodikal NY Backend
Uses Cloudflare Workers KV for distributed rate limit tracking
"""
from typing import Optional, Tuple
from js import Date


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class RateLimiter:
    """Rate limiter using Cloudflare Workers KV"""

    def __init__(self, kv_namespace):
        """
        Initialize rate limiter

        Args:
            kv_namespace: Cloudflare Workers KV namespace binding
        """
        self.kv = kv_namespace

    async def check_rate_limit(self, ip: str, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """
        Check if rate limit is exceeded

        Args:
            ip: Client IP address
            key: Rate limit key (e.g., "auth_fail", "create_order")
            limit: Maximum number of requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        if not ip or not self.kv:
            # If no IP or KV, allow the request (fail open)
            return True, 0

        # Create unique key for this IP and rate limit type
        rate_key = f"rate:{key}:{ip}"

        try:
            # Get current count and timestamp from KV
            value = await self.kv.get(rate_key)

            # Use JavaScript Date.now() for current timestamp (milliseconds since epoch)
            # Convert to seconds to match Python time.time() behavior
            current_time = int(Date.now() / 1000)

            if value:
                # Parse stored value: "count:timestamp"
                parts = value.split(':')
                if len(parts) == 2:
                    count = int(parts[0])
                    timestamp = int(parts[1])

                    # Check if we're still within the time window
                    elapsed = current_time - timestamp

                    if elapsed < window:
                        # Still within window
                        if count >= limit:
                            # Rate limit exceeded
                            retry_after = window - elapsed
                            return False, retry_after
                        else:
                            # Increment counter
                            new_count = count + 1
                            await self.kv.put(
                                rate_key,
                                f"{new_count}:{timestamp}",
                                expirationTtl=window
                            )
                            return True, 0
                    else:
                        # Window expired, start new window
                        await self.kv.put(
                            rate_key,
                            f"1:{current_time}",
                            expirationTtl=window
                        )
                        return True, 0

            # No existing record, start new window
            await self.kv.put(
                rate_key,
                f"1:{current_time}",
                expirationTtl=window
            )
            return True, 0

        except Exception as e:
            # On error, fail open (allow request)
            print(f"Rate limit check error: {str(e)}")
            return True, 0

    async def record_failed_auth(self, ip: str) -> Tuple[bool, int]:
        """
        Record failed authentication attempt

        Args:
            ip: Client IP address

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        # 5 failed attempts per 15 minutes (900 seconds)
        return await self.check_rate_limit(ip, "auth_fail", 5, 900)

    async def check_admin_rate_limit(self, ip: str) -> Tuple[bool, int]:
        """
        Check rate limit for admin endpoints

        Args:
            ip: Client IP address

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        # 60 requests per minute
        return await self.check_rate_limit(ip, "admin", 60, 60)

    async def check_order_creation_rate_limit(self, ip: str) -> Tuple[bool, int]:
        """
        Check rate limit for order creation

        Args:
            ip: Client IP address

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        # 10 orders per minute (prevents spam)
        return await self.check_rate_limit(ip, "create_order", 10, 60)

    async def check_promo_validation_rate_limit(self, ip: str) -> Tuple[bool, int]:
        """
        Check rate limit for promo code validation

        Args:
            ip: Client IP address

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        # 30 validations per minute
        return await self.check_rate_limit(ip, "validate_promo", 30, 60)

    async def check_public_api_rate_limit(self, ip: str) -> Tuple[bool, int]:
        """
        Check rate limit for public API endpoints (menu)

        Args:
            ip: Client IP address

        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        # 100 requests per minute
        return await self.check_rate_limit(ip, "public_api", 100, 60)
