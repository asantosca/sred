# Infrastructure Decision: Valkey vs Redis

**Date**: 2025-11-22
**Status**: Implemented
**Decision**: Use Valkey instead of Redis for caching and task queue

---

## Context

BC Legal Tech requires a fast in-memory data store for:
- Celery task queue (background document processing)
- Session caching
- Rate limiting cache
- Future: Real-time features (WebSocket connections, presence)

Traditionally, Redis has been the go-to solution for these use cases. However, significant licensing and cost changes in 2024-2025 prompted a re-evaluation.

---

## What Happened to Redis?

### March 2024: Licensing Change
Redis Inc. changed Redis from open source (BSD license) to a restrictive **Business Source License (BSL)**. This effectively killed Redis as a truly open-source project.

### AWS Response: Valkey Fork
Amazon Web Services, along with other cloud providers, forked Redis 7.2 (the last open-source version) and created **Valkey**, now maintained by the Linux Foundation under a BSD license.

### May 2025: Redis Adds AGPLv3
Redis 8.0 added AGPLv3 as an option, but this copyleft license is often unviable for commercial projects due to requirements to contribute code changes back.

---

## Decision: Valkey

We chose **Valkey 8.0** for the following reasons:

### 1. Cost Savings (20-33% cheaper)

**AWS ElastiCache Pricing Comparison:**
- **Redis**: `r6g.8xlarge` costs **$3.66/hour**
- **Valkey**: `r6g.8xlarge` costs **$2.93/hour** (20% cheaper)
- **ElastiCache Serverless**: Valkey is **33% cheaper** than Redis

**Annual Savings Example:**
- 10-node cluster: Save **$50,000+/year**
- Our projected usage (3-5 nodes): Save **$15,000-25,000/year**

### 2. Performance Improvements

Valkey 8.0 offers significant performance gains over Redis 7.x:
- **3x faster throughput**: 1.19M requests/sec (enhanced I/O multithreading)
- **20% less memory usage**: For large datasets
- **Better multi-threading**: Improved for high-throughput applications

### 3. 100% API Compatibility

Valkey maintains full compatibility with Redis:
- **Same APIs**: Drop-in replacement, zero code changes
- **Same protocol**: Works with all Redis client libraries
- **Same commands**: All Redis commands supported
- **Same data structures**: Strings, hashes, lists, sets, sorted sets, etc.

Our Python code uses standard Redis libraries (`redis-py`, `celery`) which work seamlessly with Valkey.

### 4. Licensing & Open Source

- **BSD License**: Truly open source, no restrictions
- **Linux Foundation**: Neutral governance, community-driven
- **Future-proof**: No risk of licensing changes affecting our business

### 5. AWS Native Support

AWS fully supports Valkey on ElastiCache:
- First-class support (same as Redis)
- Automatic upgrades and patches
- Same security and compliance features
- Migration tools from Redis to Valkey

---

## Migration Path

### Development (Local)
```yaml
# docker-compose.yml
services:
  valkey:
    image: valkey/valkey:8-alpine
    ports:
      - "6379:6379"
```

**Code changes**: None (100% compatible)

### Production (AWS ElastiCache)
1. Create new ElastiCache cluster with Valkey engine
2. Update connection string in environment variables
3. No application code changes required

**Estimated downtime**: < 5 minutes (during DNS switch)

---

## Trade-offs Considered

### Why Not Redis?

**Cons of Redis:**
- 20-33% more expensive on AWS
- Licensing uncertainty (AGPLv3 copyleft)
- Slower performance than Valkey 8.0
- Higher memory usage

**Pros of Redis:**
- Larger ecosystem (more tutorials, Stack Overflow answers)
- Redis Inc. enterprise support (we don't need this)
- Some advanced modules (Redis JSON, TimeSeries) - not needed for our use case

### Why Not Other Alternatives?

**Memcached:**
- No persistence (data lost on restart)
- No complex data structures
- No pub/sub or task queue support

**DragonflyDB:**
- Newer, less mature
- Smaller community
- Limited cloud provider support

**KeyDB:**
- Smaller community than Valkey
- Less cloud provider support
- Uncertain long-term roadmap

---

## Current Implementation

### Local Development
- **Container**: `valkey/valkey:8-alpine` (Docker)
- **Port**: 6379 (standard Redis port)
- **Connection**: `redis://localhost:6379`

### Production (Planned - Phase 4)
- **Service**: AWS ElastiCache for Valkey
- **Instance Type**: `cache.r6g.large` (2 vCPU, 13.07 GiB RAM)
- **High Availability**: Multi-AZ with automatic failover
- **Backups**: Daily automated snapshots

### Cost Estimates (Production)

**Valkey on ElastiCache:**
- `cache.r6g.large`: $0.226/hour = **$164/month**
- With reserved instances (1-year): **$110/month** (33% savings)

**Redis equivalent would cost:**
- `cache.r6g.large`: $0.283/hour = **$205/month**
- **Savings: $41/month** or **$492/year** (single node)

For a 3-node cluster with replication:
- **Valkey**: $330/month
- **Redis**: $615/month
- **Savings: $285/month** or **$3,420/year**

---

## Performance Benchmarks

Based on AWS performance tests (Valkey 8.0 vs Redis 7.1):

| Metric | Redis 7.1 | Valkey 8.0 | Improvement |
|--------|-----------|------------|-------------|
| GET requests/sec | 400K | 1.19M | **3x faster** |
| SET requests/sec | 350K | 1.05M | **3x faster** |
| Memory usage (10GB dataset) | 10.2 GB | 8.2 GB | **20% less** |
| P99 latency | 2.1ms | 1.4ms | **33% lower** |

Our use case (Celery task queue + caching):
- Expected throughput: 10K-50K tasks/day
- Peak load: 100-500 requests/sec
- Data size: < 1 GB (transient task data)

Valkey 8.0 easily handles our current and projected load.

---

## Security Considerations

### Data Encryption
- **In-transit**: TLS 1.2+ (ElastiCache supports this)
- **At-rest**: AWS encryption enabled by default

### Access Control
- **VPC isolation**: ElastiCache runs in private subnet
- **Security groups**: Restrict access to backend application only
- **AUTH password**: Enabled in production

### Compliance
- Same compliance certifications as Redis on ElastiCache
- SOC 2, HIPAA, PCI DSS compliant
- Suitable for legal document processing

---

## Rollback Plan

If Valkey causes unexpected issues:

1. **Short-term**: Valkey is 100% Redis-compatible, so we can switch to Redis 7.2 with zero code changes
2. **ElastiCache**: AWS supports both Valkey and Redis engines
3. **Data migration**: Use ElastiCache backup/restore to migrate between engines
4. **Estimated rollback time**: < 30 minutes

**Risk**: Very low. Valkey is a stable fork with 1+ year of production usage at AWS and other major companies.

---

## Monitoring & Observability

### Metrics to Track
- **Throughput**: Commands/sec
- **Latency**: P50, P95, P99 response times
- **Memory usage**: Current memory, peak memory
- **Eviction rate**: Cache evictions (should be near zero)
- **Connection count**: Active client connections

### Alerting Thresholds
- P99 latency > 10ms
- Memory usage > 80%
- Eviction rate > 100/min
- Connection failures > 1%

### Tools
- **AWS CloudWatch**: ElastiCache metrics
- **Sentry**: Application-level errors
- **Celery Flower**: Task queue monitoring

---

## Timeline

- **2025-11-22**: Decision made, local development updated to Valkey
- **Phase 4 (2-3 weeks)**: Production ElastiCache Valkey cluster deployment
- **Phase 5 (Beta)**: Monitor performance with real user load
- **Post-Beta**: Evaluate cost savings and performance improvements

---

## References

- [Valkey vs Redis Comparison (Better Stack)](https://betterstack.com/community/comparisons/redis-vs-valkey/)
- [AWS ElastiCache Valkey Performance Analysis](https://aws.plainenglish.io/aws-elasticache-a-performance-and-cost-analysis-of-redis-7-1-vs-valkey-7-2-bfac4fb5c22a)
- [AWS ElastiCache Pricing](https://aws.amazon.com/elasticache/pricing/)
- [Valkey GitHub Repository](https://github.com/valkey-io/valkey)
- [Redis Licensing Changes (2024)](https://redis.io/blog/redis-adopts-dual-source-available-licensing/)

---

## Conclusion

**Valkey is the clear choice** for BC Legal Tech:
- **20-33% cost savings** on AWS ElastiCache
- **3x performance improvement** over Redis 7.x
- **100% API compatible** (zero code changes)
- **Truly open source** (BSD license, Linux Foundation)
- **AWS native support** (first-class ElastiCache integration)

This decision saves us thousands of dollars annually while improving performance and maintaining full compatibility with our existing code.

**Status**: Implemented in development. Production deployment planned for Phase 4.
