AHOS UNIVERSAL MARKET OBJECT STANDARD
Version 1.0
Classification: Internal Architecture Standard
Status: Official
Prepared by: Chief Software Architect
Audience: All AHOS Engineering Teams

================================================================================
PREAMBLE
================================================================================

This document defines the AHOS Universal Market Object (UMO) Standard v1.0. The UMO is the single canonical data structure that represents one tradeable market pair within the AHOS platform. Every component of AHOS that produces, consumes, transforms, stores, or transmits market pair data must conform to this standard without exception.

The UMO is not a database schema. It is not an API contract. It is the platform-wide semantic agreement about what constitutes a market pair record and what every field within that record means. Database schemas, API contracts, message queue payloads, and inter-workflow data structures must all be derived from the UMO. The UMO is the source of truth from which all derived representations are generated, not the reverse.

The motivation for the UMO is architectural. AHOS ingests market data from sources that have fundamentally different data models, field naming conventions, numeric precision behaviors, timestamp formats, and completeness guarantees. Without a canonical object, every component that consumes market data must understand every source's schema and handle every source's idiosyncrasies independently. This creates a combinatorial maintenance burden that becomes unmanageable as new sources are added. The UMO eliminates this burden by defining a single target representation that all source-specific data is mapped into at the earliest possible point in the pipeline.

Every field defined in this standard has been designed with the following principles: semantic precision over syntactic convenience, explicit over implicit, present-but-null over absent, typed over untyped, and versioned over static.

================================================================================
SECTION 1 — CORE OBJECT STRUCTURE
================================================================================

The AHOS Universal Market Object is a hierarchical structured record. It is organized into a flat identity layer and nine semantic sections. The identity layer contains fields that uniquely identify the object and its provenance. The semantic sections organize the remaining fields by their functional domain.

The top-level structure is as follows:

Identity Layer (top-level fields, not nested):
These fields exist at the root of the object and are accessible without traversing any nested structure. They are the minimum fields required to route, store, deduplicate, and correlate any UMO instance across the platform.

umo_id
umo_version
object_type
created_at
updated_at
pair_id
pair_address
chain_id
dex_id
collector_id
source_id
collection_run_id
job_id
ingest_timestamp
schema_version

Semantic Sections (nested objects):
Each semantic section is a named nested object within the UMO. All fields belonging to a functional domain are grouped within their section. Cross-section references are expressed through the identity layer fields only. Sections never reference other sections directly to avoid circular dependencies and to allow any section to be processed, stored, or transmitted independently.

The nine semantic sections are:

token — describes the base token being traded
quote — describes the quote token paired against the base token
market — describes the market-level characteristics of this pair
price — describes all price-related data points for this pair
liquidity — describes the liquidity state of this pair's pool
volume — describes trading volume across multiple time windows
risk — describes risk indicators observable at collection time
social — describes social signal data associated with the base token
discovery — describes the discovery context in which this pair was found
quality — describes the data quality assessment of this UMO instance
metadata — describes the collection and processing provenance of this UMO instance

================================================================================
SECTION 2 — REQUIRED FIELDS
================================================================================

Required fields are fields that must be present and non-null in every UMO instance. A UMO instance that is missing any required field is considered malformed and must be rejected by any consuming component without partial processing. Required fields are the minimum viable representation of a market pair for AHOS purposes.

The designation of a field as required does not mean the source always provides it. It means that if a valid value cannot be determined for this field from the source data or from derivation logic, the entire UMO instance must not be created and the pair must be counted as skipped.

Required fields are defined as follows:

From the Identity Layer:
umo_id must be present. This is the platform-generated unique identifier for this specific UMO instance.
umo_version must be present. This identifies the version of the UMO standard this instance conforms to.
pair_address must be present. This is the on-chain contract address of the liquidity pool or pair.
chain_id must be present. This identifies the blockchain on which this pair exists.
dex_id must be present. This identifies the decentralized exchange on which this pair is listed.
collector_id must be present. This identifies the AHOS collector that produced this UMO instance.
source_id must be present. This identifies the external data source from which the raw data was obtained.
ingest_timestamp must be present. This records the moment the raw data entered the AHOS pipeline.

From the token section:
token.address must be present. This is the on-chain contract address of the base token.
token.symbol must be present. This is the ticker symbol of the base token.

From the price section:
price.usd must be present. A null value is acceptable only if the pair has zero trading activity and the null is explicitly justified in the quality section. In all other cases, a non-null numeric value is required.

From the quality section:
quality.is_valid must be present. This boolean field indicates whether this UMO instance passed all quality validation checks.
quality.validation_timestamp must be present. This records when quality validation was performed.

================================================================================
SECTION 3 — OPTIONAL FIELDS
================================================================================

Optional fields are fields that may be null or absent without causing a UMO instance to be considered malformed. Optional fields become populated as more data sources contribute to the UMO instance through the enrichment pipeline or when the primary source provides the data.

Optional fields must still conform to their defined types and validation rules when present. An optional field with a value that fails type or range validation is treated as a data quality issue recorded in the quality section, not as grounds for rejecting the entire UMO instance.

The following fields are optional and may be null in a valid UMO instance:

From the Identity Layer:
collection_run_id — may be null when the UMO is created through a manual or event-triggered collection outside of a scheduled run.
job_id — may be null in the same circumstances as collection_run_id.

From the token section:
token.name — the full name of the base token.
token.decimals — the number of decimal places in the base token's smallest unit.
token.total_supply — the total token supply.
token.circulating_supply — the circulating token supply.
token.logo_uri — the URI of the token's logo image.
token.website — the token project's website URL.
token.coingecko_id — the token's identifier on CoinGecko if listed.
token.coinmarketcap_id — the token's identifier on CoinMarketCap if listed.

From the quote section:
All quote section fields except quote.symbol and quote.address are optional.

From the market section:
market.fdv — fully diluted valuation, optional when supply data is unavailable.
market.market_cap — market capitalization, optional when circulating supply is unavailable.
market.rank — the token's market rank if available from aggregator sources.
market.listed_at — the timestamp when the token was first listed on a major aggregator.

From the price section:
price.native — the price expressed in the quote token's native units.
price.change_5m — price change percentage over 5 minutes.
price.change_1h — price change percentage over 1 hour.
price.change_6h — price change percentage over 6 hours.
price.change_24h — price change percentage over 24 hours.
price.high_24h — highest price in the past 24 hours.
price.low_24h — lowest price in the past 24 hours.
price.ath — all-time high price in USD.
price.ath_timestamp — timestamp when the all-time high was recorded.

From the liquidity section:
All liquidity section fields except liquidity.usd are optional.

From the volume section:
volume.m5 — trading volume over 5 minutes.
volume.h1 — trading volume over 1 hour.
volume.h6 — trading volume over 6 hours.
volume.h24 — trading volume over 24 hours. This field is strongly recommended and treated as high-priority optional.
volume.buys_24h — count of buy transactions in 24 hours.
volume.sells_24h — count of sell transactions in 24 hours.
volume.buy_volume_24h — total buy-side volume in USD over 24 hours.
volume.sell_volume_24h — total sell-side volume in USD over 24 hours.

From the risk section:
All risk section fields are optional at collection time. They are populated by Phase 3 enrichment.

From the social section:
All social section fields are optional. They are populated by the social intelligence collector.

From the discovery section:
discovery.signals — the array of discovery signals triggered for this pair.
discovery.priority_score — the pre-AI priority score.

================================================================================
SECTION 4 — METADATA SECTION
================================================================================

The metadata section records the complete provenance chain of a UMO instance. It answers: where did this data come from, when was it collected, how was it processed, and what is its lineage within the AHOS pipeline.

The metadata section contains the following fields:

metadata.source_name
Type: String
Description: The human-readable name of the external data source that provided the raw data for this UMO instance. Examples: DexScreener, GeckoTerminal, Birdeye, GMGN, Pump.fun, Raydium, Jupiter.
Required: Yes

metadata.source_version
Type: String
Description: The version identifier of the source API or data format from which this data was collected. This is not the AHOS UMO version. It is the version of the external source's data format, if the source exposes such information. If the source does not expose a version identifier, this field contains the date of the API endpoint specification used to build the parser, expressed as an ISO 8601 date string.
Required: Yes

metadata.source_endpoint
Type: String
Description: The specific API endpoint or data feed identifier from which the raw data was collected. This is the normalized form of the endpoint, with path parameters replaced by their semantic labels. For example, a DexScreener endpoint would be recorded as pairs/chain/{chainId} rather than the literal URL with the chain identifier substituted.
Required: Yes

metadata.collection_timestamp
Type: String, ISO 8601 UTC datetime
Description: The timestamp at which the Collection Execution Module dispatched the HTTP request or initiated the data stream connection that produced the raw data for this UMO instance. This is distinct from ingest_timestamp, which records when the raw data arrived in the AHOS pipeline. collection_timestamp records when the request was sent.
Required: Yes

metadata.ingest_timestamp
Type: String, ISO 8601 UTC datetime
Description: The timestamp at which the raw API response was written to the AHOS raw ingestion archive. This is the authoritative time-of-receipt for this data.
Required: Yes

metadata.normalization_timestamp
Type: String, ISO 8601 UTC datetime
Description: The timestamp at which the Normalization Module completed transformation of the raw source data into this UMO instance.
Required: Yes

metadata.parser_id
Type: String
Description: The identifier of the parser class that transformed the raw source data into this UMO instance. This is the parser's registered identifier in the AHOS Parser Registry, not its class name. Example format: dexscreener-pairs-v2, geckoTerminal-ohlcv-v1.
Required: Yes

metadata.parser_version
Type: String
Description: The version of the parser that produced this UMO instance. Parser versions follow semantic versioning. This field enables correlation between parser version changes and data quality changes.
Required: Yes

metadata.raw_archive_reference
Type: String
Description: The key or identifier of the raw archive record from which this UMO instance was derived. This enables reconstruction of the raw source data from which any UMO instance was produced, which is essential for debugging parser issues and reprocessing after parser updates.
Required: Yes

metadata.collection_run_id
Type: String, nullable
Description: The identifier of the scheduled collection run that triggered this UMO instance's collection. Null when the collection was triggered manually or by an event outside the scheduler.
Required: No

metadata.job_id
Type: String, nullable
Description: The identifier of the specific collection job within the collection run that produced this UMO instance.
Required: No

metadata.chain_requested
Type: String
Description: The chain identifier that was specified in the collection job at dispatch time. This may differ from chain_id if the source returned data for an unexpected chain. The presence of a difference between chain_requested and chain_id is a data quality flag.
Required: Yes

metadata.collector_version
Type: String
Description: The version of the AHOS collector component that executed this collection. Follows semantic versioning.
Required: Yes

metadata.enrichment_history
Type: Array of enrichment records
Description: An ordered list of all enrichment operations that have been applied to this UMO instance since its creation. Each enrichment record contains: enrichment_id (string), enrichment_source (string identifying the enricher), enrichment_timestamp (ISO 8601 UTC string), fields_added (array of dot-notation field paths), fields_updated (array of dot-notation field paths), and enrichment_version (string). This array is empty on initial creation and grows as the UMO instance passes through Phase 3 and subsequent enrichment stages.
Required: Yes, initialized as empty array

metadata.deduplication_key
Type: String
Description: The canonical deduplication key computed for this UMO instance. The deduplication key is the concatenation of chain_id and pair_address with a defined separator. This field is stored for auditing purposes so that the deduplication logic applied to this instance can be verified independently.
Required: Yes

metadata.merge_history
Type: Array of merge records, nullable
Description: When a UMO instance is the result of merging data from multiple sources, this array records each merge event. Each merge record contains: merge_timestamp (ISO 8601 UTC string), merged_source_id (string), merged_umo_id (string), fields_affected (array of dot-notation field paths), and field_authority_applied (string identifying the authority rule used). Null when no merging has occurred.
Required: No

================================================================================
SECTION 5 — MARKET SECTION
================================================================================

The market section describes the macro-level market characteristics of the pair. These are high-level metrics that describe the pair's standing in the broader market context rather than its moment-to-moment trading state.

market.fdv
Type: Number, nullable, non-negative
Description: Fully diluted valuation expressed in USD. Calculated as the current price in USD multiplied by the total token supply. Null when total supply is not available from any source contributing to this UMO instance.
Source mapping: DexScreener provides fdv directly. GeckoTerminal provides it in the market data section. Birdeye provides it as fdv. Sources that do not provide it require derivation from price.usd multiplied by token.total_supply when both are available.

market.market_cap
Type: Number, nullable, non-negative
Description: Market capitalization expressed in USD. Calculated as the current price in USD multiplied by the circulating supply. Null when circulating supply is not available. Market cap and FDV are distinguished explicitly because the difference between them is a material signal for discovery purposes.
Source mapping: Varies by source. When not directly provided, derivation from price.usd multiplied by token.circulating_supply is attempted. When neither circulating supply nor market cap is available, this field is null.

market.rank
Type: Integer, nullable, positive
Description: The token's global market rank by market capitalization as provided by aggregator-class sources. This field is only populated when the UMO instance has been enriched by a CoinGecko or CoinMarketCap source. Null for tokens not yet tracked by major aggregators.

market.pair_age_seconds
Type: Integer, nullable, non-negative
Description: The age of the trading pair in seconds, calculated as the difference between ingest_timestamp and pair_created_at at normalization time. This is a derived field. It is explicitly calculated and stored rather than computed on-demand because pair age is a primary signal for the Discovery Engine's new launch and recent launch signal categories, and recomputing it downstream introduces timestamp interpretation ambiguity.

market.pair_created_at
Type: String, ISO 8601 UTC datetime, nullable
Description: The timestamp at which the liquidity pool or pair contract was deployed on-chain or when the pair first became active on the DEX. The precision and source of this timestamp varies by data source. When multiple sources provide conflicting creation timestamps, the earliest value is stored and the conflict is recorded in the quality section.

market.listed_at
Type: String, ISO 8601 UTC datetime, nullable
Description: The timestamp at which this token first appeared on a major aggregator-class source such as CoinGecko or CoinMarketCap. Null until aggregator enrichment occurs. This timestamp represents a material moment in a token's lifecycle because aggregator listing triggers broader market discovery.

market.transactions_24h
Type: Integer, nullable, non-negative
Description: The total number of on-chain transactions involving this pair in the past 24 hours. Includes both buy and sell sides. When source data separates buys and sells, this field is derived as the sum of volume.buys_24h and volume.sells_24h when the source does not provide a combined count.

market.unique_wallets_24h
Type: Integer, nullable, non-negative
Description: The number of unique wallet addresses that interacted with this pair in the past 24 hours. This is an on-chain enrichment field populated by explorer-class sources such as Solscan, Etherscan, or BscScan. Null at initial collection from DEX-class sources.

market.price_impact_estimate
Type: Number, nullable, non-negative
Description: An estimate of the price impact percentage for a standardized trade size against the current liquidity. The standardized trade size is defined in the AHOS configuration as a chain-specific USD value representing a reference trade. This field is calculated during enrichment when sufficient liquidity data is available.

================================================================================
SECTION 6 — TOKEN SECTION
================================================================================

The token section describes the base token in the trading pair. The base token is the token being priced and analyzed. In a SOL/USDC pair analyzing a new Solana token, the new token is the base token and USDC is the quote token.

token.address
Type: String, non-null, non-empty
Description: The on-chain contract address of the base token. This is a required field. The format varies by chain: EVM chains use checksummed hex addresses prefixed with 0x, Solana uses base58 public keys. The address is stored in its canonical format for the chain as defined in the AHOS chain format registry. Addresses are never normalized to lowercase because checksum information is semantically significant for EVM chains.

token.symbol
Type: String, non-null, non-empty
Description: The ticker symbol of the base token as reported by the primary data source. This is a required field. Symbols are stored without normalization of case because case may be semantically meaningful to the token's identity. Leading and trailing whitespace is trimmed. The maximum length is 32 characters. Symbols exceeding 32 characters are truncated and the truncation is recorded in the quality section.

token.name
Type: String, nullable
Description: The full display name of the base token as reported by the primary data source. Leading and trailing whitespace is trimmed. The maximum length is 256 characters. Names exceeding 256 characters are truncated and the truncation is recorded in the quality section.

token.decimals
Type: Integer, nullable, range 0 to 18
Description: The number of decimal places used by the token's smallest on-chain unit. For EVM tokens this is the value returned by the decimals() function of the ERC-20 contract. For Solana tokens this is the decimals field in the token mint account. Values outside the range of 0 to 18 are treated as data quality failures. This field is populated from on-chain explorer sources when not provided by the primary DEX-class source.

token.total_supply
Type: Number, nullable, non-negative
Description: The total number of tokens in existence, expressed in whole token units (not smallest units). This is the circulating plus locked plus burned supply. Expressed as a floating-point number because token supplies can exceed JavaScript's safe integer range and because the field must accommodate partial supply figures.

token.circulating_supply
Type: Number, nullable, non-negative
Description: The number of tokens currently in circulation and not locked, vested, or burned. Expressed in whole token units. This field has lower data availability than total_supply because many DEX-class sources do not track circulating supply. It is populated primarily through aggregator-class source enrichment.

token.logo_uri
Type: String, nullable
Description: The URI of the token's logo image. Stored as provided by the source without validation of accessibility. The presence or absence of a logo URI is itself a signal used in the quality assessment.

token.website
Type: String, nullable
Description: The primary website URL of the token project. Stored as provided by the source. URL format validation is applied: the value must begin with https:// to be stored. Values beginning with http:// are converted to https:// if the URL is otherwise valid. Values that are not valid URLs are stored as null with the data quality issue recorded.

token.coingecko_id
Type: String, nullable
Description: The token's identifier on the CoinGecko platform, used for cross-reference and for constructing CoinGecko API requests during enrichment. This field is populated only after aggregator enrichment. Its presence indicates the token has achieved CoinGecko listing, which is a material market maturity signal.

token.coinmarketcap_id
Type: String, nullable
Description: The token's numeric identifier on the CoinMarketCap platform. Stored as a string because it is used as an identifier rather than for arithmetic. Same lifecycle as coingecko_id.

token.is_verified
Type: Boolean, nullable
Description: Indicates whether the token contract has been verified on its chain's primary explorer. True means the contract source code is publicly available and matches the deployed bytecode. False means it is not verified. Null means verification status has not yet been checked. This field is populated by explorer-class source enrichment.

token.deployer_address
Type: String, nullable
Description: The on-chain address of the wallet that deployed the base token contract. This field is populated by explorer-class source enrichment and is a key input for Phase 3 risk analysis.

token.deploy_timestamp
Type: String, ISO 8601 UTC datetime, nullable
Description: The timestamp of the on-chain transaction that deployed the base token contract. This is distinct from market.pair_created_at, which records when the trading pair was created. A significant gap between token deployment and pair creation may be a risk signal. Populated by explorer-class source enrichment.

================================================================================
SECTION 7 — QUOTE SECTION
================================================================================

The quote section describes the quote token in the trading pair. The quote token is the token against which the base token is priced. Common quote tokens include USDC, USDT, WETH, WBNB, SOL, and WBTC.

quote.address
Type: String, nullable
Description: The on-chain contract address of the quote token. Format rules are identical to token.address. Nullable because some sources represent native chain tokens such as ETH or SOL as quote tokens without a contract address, using a sentinel value or omitting the address entirely. When the quote token is the native chain token, this field is null and quote.is_native is true.

quote.symbol
Type: String, non-null, non-empty
Description: The ticker symbol of the quote token. Required because the quote token symbol is necessary to understand the pair's market context. A pair quoted against USDC has a different market interpretation than a pair quoted against SOL, and this distinction is required for correct price normalization in downstream analysis.

quote.name
Type: String, nullable
Description: The full display name of the quote token.

quote.decimals
Type: Integer, nullable, range 0 to 18
Description: The decimal precision of the quote token. Follows identical rules to token.decimals.

quote.is_native
Type: Boolean, non-null
Description: True when the quote token is the native gas token of the chain, such as ETH on Ethereum, BNB on BSC, or SOL on Solana. False in all other cases. This field is never null. It defaults to false and is set to true when the source data indicates a native token quote or when the quote address matches the chain's registered native token sentinel address in the AHOS chain registry.

quote.is_stablecoin
Type: Boolean, non-null
Description: True when the quote token is a recognized stablecoin pegged to a fiat currency. The determination of stablecoin status is made against the AHOS stablecoin registry, which is a maintained list of known stablecoin contract addresses per chain. False in all other cases. This field is never null. It defaults to false.

================================================================================
SECTION 8 — LIQUIDITY SECTION
================================================================================

The liquidity section describes the state of liquidity in the pair's pool. Liquidity data is one of the most critical signals for the Discovery Engine because both the absolute level and the rate of change of liquidity are primary discovery triggers.

liquidity.usd
Type: Number, nullable, non-negative
Description: The total liquidity of the pair's primary pool expressed in USD. This is the sum of the USD value of both sides of the liquidity pool at the collection timestamp. This is a strongly recommended field and is required for most Discovery Engine signal rules. Null indicates the source did not provide liquidity data. Zero indicates genuinely zero liquidity, which must be distinguished from null.

liquidity.base
Type: Number, nullable, non-negative
Description: The quantity of the base token held in the liquidity pool, expressed in whole base token units. This is the raw on-chain quantity, not its USD equivalent.

liquidity.quote
Type: Number, nullable, non-negative
Description: The quantity of the quote token held in the liquidity pool, expressed in whole quote token units.

liquidity.base_usd
Type: Number, nullable, non-negative
Description: The USD value of the base token portion of the liquidity pool. When provided by the source, this value is stored directly. When not provided, it is derived as liquidity.base multiplied by price.usd when both fields are available.

liquidity.quote_usd
Type: Number, nullable, non-negative
Description: The USD value of the quote token portion of the liquidity pool. When provided by the source, this value is stored directly. When not provided, it is derived as liquidity.usd minus liquidity.base_usd when both parent fields are available.

liquidity.pool_count
Type: Integer, nullable, positive
Description: The total number of distinct liquidity pools for this pair across all DEX venues on the same chain. This is populated when aggregator-class sources provide cross-venue aggregation. A single pair existing in multiple pools simultaneously is a signal of market maturity or of deliberate multi-venue liquidity provision.

liquidity.locked_usd
Type: Number, nullable, non-negative
Description: The USD value of liquidity that has been locked in a time-lock contract, as reported by sources that provide lock information. Null when lock data is unavailable. The ratio of locked_usd to usd is a risk mitigation signal.

liquidity.lock_expiry
Type: String, ISO 8601 UTC datetime, nullable
Description: The timestamp at which the earliest liquidity lock on this pair expires. When multiple locks exist with different expiry times, this field stores the earliest (soonest) expiry, which represents the earliest point at which locked liquidity could be removed.

liquidity.change_1h_pct
Type: Number, nullable
Description: The percentage change in total USD liquidity over the past 1 hour. Positive values indicate liquidity addition. Negative values indicate liquidity removal. This is a primary signal for the abnormal liquidity growth signal category. Calculated during enrichment when historical liquidity snapshots are available.

liquidity.change_24h_pct
Type: Number, nullable
Description: The percentage change in total USD liquidity over the past 24 hours. Follows the same rules as change_1h_pct.

================================================================================
SECTION 9 — VOLUME SECTION
================================================================================

The volume section describes trading volume across multiple time windows. Volume data is used for both the abnormal volume signal category and for market maturity assessment.

All volume fields represent USD-denominated trading volume unless explicitly suffixed with _native, in which case they represent volume expressed in the quote token's units.

volume.m5
Type: Number, nullable, non-negative
Description: Total trading volume over the most recent 5-minute window, expressed in USD. The 5-minute window is the shortest standard window used by AHOS and reflects the most recent market activity. High values relative to longer windows indicate accelerating activity.

volume.h1
Type: Number, nullable, non-negative
Description: Total trading volume over the most recent 1-hour window, expressed in USD.

volume.h6
Type: Number, nullable, non-negative
Description: Total trading volume over the most recent 6-hour window, expressed in USD.

volume.h24
Type: Number, nullable, non-negative
Description: Total trading volume over the most recent 24-hour window, expressed in USD. This is the most commonly available volume metric across all sources and is the primary volume field used by Discovery Engine signal rules.

volume.buys_m5
Type: Integer, nullable, non-negative
Description: Count of buy-side transactions in the most recent 5-minute window.

volume.sells_m5
Type: Integer, nullable, non-negative
Description: Count of sell-side transactions in the most recent 5-minute window.

volume.buys_h1
Type: Integer, nullable, non-negative
Description: Count of buy-side transactions in the most recent 1-hour window.

volume.sells_h1
Type: Integer, nullable, non-negative
Description: Count of sell-side transactions in the most recent 1-hour window.

volume.buys_h24
Type: Integer, nullable, non-negative
Description: Count of buy-side transactions in the most recent 24-hour window.

volume.sells_h24
Type: Integer, nullable, non-negative
Description: Count of sell-side transactions in the most recent 24-hour window.

volume.buy_volume_h24
Type: Number, nullable, non-negative
Description: The total USD value of buy-side transactions in the most recent 24-hour window. This is distinct from the count of buy transactions. The combination of buys_h24 and buy_volume_h24 allows calculation of the average buy transaction size, which is a behavioral signal.

volume.sell_volume_h24
Type: Number, nullable, non-negative
Description: The total USD value of sell-side transactions in the most recent 24-hour window.

volume.buy_sell_ratio_h24
Type: Number, nullable, non-negative
Description: The ratio of buy-side volume to sell-side volume over the past 24 hours. Calculated as buy_volume_h24 divided by sell_volume_h24 when both are available and sell_volume_h24 is non-zero. A value greater than 1.0 indicates net buying pressure. A value less than 1.0 indicates net selling pressure. When sell_volume_h24 is zero and buy_volume_h24 is positive, this field stores a sentinel value defined in the AHOS configuration, typically a very large number, with the edge case recorded in the quality section. When both are zero, this field is null.

volume.anomaly_score
Type: Number, nullable, range 0.0 to 1.0
Description: A normalized score representing how anomalous the current volume is relative to the historical baseline for this pair. Calculated during Phase 3 enrichment using the historical volume data stored in the AHOS historical knowledge base. Zero indicates volume exactly matches the historical baseline. One indicates the maximum anomaly magnitude defined in the scoring model. This field is null at collection time and populated only after historical comparison enrichment.

================================================================================
SECTION 10 — PRICE SECTION
================================================================================

The price section consolidates all price-related data points. Price data is the most frequently updated data in the market ecosystem and is subject to the highest staleness risk of any UMO section.

price.usd
Type: Number, nullable, non-negative
Description: The current price of the base token expressed in USD at the collection timestamp. This is a required field except when price.usd_unavailable_reason is populated with an explicit justification. The value is stored with full floating-point precision as provided by the source. No rounding is applied at the UMO layer. Rounding for display or analysis purposes is the responsibility of the consuming component.

price.native
Type: Number, nullable, non-negative
Description: The current price of the base token expressed in units of the quote token. For a pair of NEW_TOKEN/USDC, this would be the price in USDC. For a pair of NEW_TOKEN/SOL, this would be the price in SOL. This field is the raw pair price before USD conversion and is preserved because USD conversion introduces exchange rate error when the quote token is not a stablecoin.

price.usd_unavailable_reason
Type: String, nullable
Description: When price.usd is null, this field must contain an explicit reason string explaining why the USD price is unavailable. Acceptable values are: ZERO_TRADING_ACTIVITY indicating the pair exists but no trades have occurred, SOURCE_NOT_PROVIDED indicating the source did not include price data, CONVERSION_FAILED indicating USD conversion was attempted but failed, and PAIR_INACTIVE indicating the pair is no longer active. When price.usd is non-null, this field must be null.

price.change_5m
Type: Number, nullable
Description: The percentage change in USD price over the past 5 minutes. Positive values indicate appreciation, negative values indicate depreciation. Expressed as a percentage where 10.5 means 10.5 percent, not 0.105.

price.change_1h
Type: Number, nullable
Description: The percentage change in USD price over the past 1 hour. Format follows price.change_5m.

price.change_6h
Type: Number, nullable
Description: The percentage change in USD price over the past 6 hours. Format follows price.change_5m.

price.change_24h
Type: Number, nullable
Description: The percentage change in USD price over the past 24 hours. This is the most widely available price change metric and is a primary input for trending signal detection.

price.high_24h
Type: Number, nullable, non-negative
Description: The highest USD price recorded for this pair in the past 24 hours. When provided by the source, stored directly. When not provided, null. Not derived from OHLCV data within the UMO parser because OHLCV derivation requires confirmed historical data from the AHOS historical knowledge base.

price.low_24h
Type: Number, nullable, non-negative
Description: The lowest USD price recorded for this pair in the past 24 hours. The relationship between high_24h and low_24h is validated: high_24h must be greater than or equal to low_24h when both are present. If this relationship is violated, both fields are set to null and the violation is recorded in the quality section.

price.ath
Type: Number, nullable, non-negative
Description: The all-time high USD price for this pair as reported by aggregator-class sources. Null for sources that do not track all-time highs. Populated through aggregator enrichment.

price.ath_timestamp
Type: String, ISO 8601 UTC datetime, nullable
Description: The timestamp at which the all-time high price was recorded. Must be present when price.ath is present. Must be null when price.ath is null.

price.precision
Type: Integer, nullable, non-negative
Description: The number of significant decimal places in the price.usd value as reported by the source. This field is used by downstream rendering and analysis components to avoid displaying spurious precision. When the source provides a price as a string such as "0.00000142", the precision is 8. When the source provides it as a number, the precision is determined by the string representation of the float.

================================================================================
SECTION 11 — RISK SECTION
================================================================================

The risk section consolidates all observable risk indicators for the pair and its base token. At collection time by the Discovery Engine, this section is primarily null. It is progressively populated as the UMO instance moves through Phase 3 enrichment, security source consultation, and AI risk analysis in Phase 4.

The presence of this section in the UMO from the moment of creation is intentional. It ensures that the risk data structure is always available and consistently shaped, regardless of which enrichment stage a given UMO instance has reached.

risk.is_honeypot
Type: Boolean, nullable
Description: True when the base token contract has been identified as a honeypot by a security source. A honeypot is a contract that allows buying but prevents or heavily taxes selling. Null when honeypot detection has not yet been performed. False when detection has been performed and the contract is confirmed not to be a honeypot. The three-state distinction between true, false, and null is critical: a null is not the same as a false.

risk.honeypot_confidence
Type: Number, nullable, range 0.0 to 1.0
Description: The confidence level of the honeypot determination when risk.is_honeypot is non-null. One indicates maximum confidence. Zero indicates minimum confidence. This field acknowledges that honeypot detection is probabilistic, not deterministic.

risk.buy_tax_pct
Type: Number, nullable, range 0.0 to 100.0
Description: The percentage of each buy transaction that is taken as a fee by the token contract. Contracts with buy taxes above the AHOS configured threshold are flagged for risk review. Sourced from security analysis services.

risk.sell_tax_pct
Type: Number, nullable, range 0.0 to 100.0
Description: The percentage of each sell transaction that is taken as a fee by the token contract. Sell taxes are a more significant risk indicator than buy taxes because they impair the ability of investors to exit positions. Contracts with sell taxes above the AHOS configured threshold are considered high risk.

risk.is_mintable
Type: Boolean, nullable
Description: True when the token contract contains a mint function that can be called by a privileged address to create new tokens. Unlimited minting capability is a risk factor because it enables the token supply to be inflated, diluting existing holders. Null until contract analysis is performed.

risk.is_proxy
Type: Boolean, nullable
Description: True when the token contract is a proxy contract whose implementation can be upgraded by a privileged address. Upgradeability is a risk factor because the contract behavior can be changed after deployment. Null until contract analysis is performed.

risk.owner_address
Type: String, nullable
Description: The current owner address of the token contract if an ownership pattern is detected. Many token contracts implement Ownable or equivalent patterns. The owner address is a key input for deployer analysis in Phase 3.

risk.ownership_renounced
Type: Boolean, nullable
Description: True when contract ownership has been renounced, meaning the owner address has been set to the zero address or an equivalent burn address. Ownership renunciation reduces but does not eliminate contract-level risk because some proxy patterns allow re-acquisition of ownership through alternative mechanisms.

risk.top_holder_pct
Type: Number, nullable, range 0.0 to 100.0
Description: The percentage of the total token supply held by the single largest holder wallet, excluding known contract addresses such as liquidity pool contracts, burn addresses, and verified exchange wallets. High top-holder concentration is a risk signal.

risk.top_10_holders_pct
Type: Number, nullable, range 0.0 to 100.0
Description: The combined percentage of the total token supply held by the ten largest holder wallets, excluding known contract addresses. Must be greater than or equal to risk.top_holder_pct when both are present.

risk.rug_pull_score
Type: Number, nullable, range 0.0 to 1.0
Description: A composite risk score representing the probability of a rug pull event, as calculated by Phase 4 AI risk models or as provided by security-class sources. Zero represents minimal rug pull risk. One represents maximum assessed rug pull risk. This field is null until risk scoring enrichment is performed.

risk.security_source_results
Type: Array of security result objects, nullable
Description: An array of raw security assessment results from each security-class source that has been consulted for this token. Each element contains: source_name (string), assessment_timestamp (ISO 8601 UTC string), risk_level (string: LOW, MEDIUM, HIGH, CRITICAL), flags (array of string flag identifiers), and source_url (string). This array preserves the complete set of security source findings without losing any individual source's assessment in the aggregation process.

risk.overall_risk_level
Type: String, nullable
Description: The aggregated risk level after considering all available risk signals. Valid values are: LOW, MEDIUM, HIGH, CRITICAL, and UNKNOWN. UNKNOWN is used when risk data is available but contradictory across sources. Null when risk assessment has not yet been performed.

================================================================================
SECTION 12 — SOCIAL SECTION
================================================================================

The social section records social signal data associated with the base token. This section is always null at initial Discovery Engine collection and is populated exclusively by the AHOS Social Intelligence Collector in subsequent pipeline stages.

social.twitter_handle
Type: String, nullable
Description: The Twitter or X platform handle of the base token project's official account, without the at-sign prefix. Sourced from token project metadata provided by sources that track social profiles.

social.twitter_followers
Type: Integer, nullable, non-negative
Description: The follower count of the token project's Twitter account at the social data collection timestamp.

social.twitter_engagement_24h
Type: Number, nullable, non-negative
Description: A normalized engagement score representing the aggregate interaction volume (likes, retweets, replies, quotes) on tweets from and about the token in the past 24 hours. The normalization methodology is defined in the Social Intelligence Collector specification.

social.telegram_url
Type: String, nullable
Description: The URL of the token project's official Telegram group or channel.

social.telegram_members
Type: Integer, nullable, non-negative
Description: The member count of the token project's Telegram group or channel at the social data collection timestamp.

social.discord_url
Type: String, nullable
Description: The URL of the token project's official Discord server.

social.discord_members
Type: Integer, nullable, non-negative
Description: The member count of the token project's Discord server at the social data collection timestamp.

social.reddit_url
Type: String, nullable
Description: The URL of the token project's official subreddit or Reddit community.

social.mention_count_24h
Type: Integer, nullable, non-negative
Description: The aggregate count of mentions of this token across all monitored social platforms in the past 24 hours.

social.sentiment_score_24h
Type: Number, nullable, range negative 1.0 to positive 1.0
Description: The aggregate sentiment score across all social mentions in the past 24 hours. Negative one indicates maximally negative sentiment. Positive one indicates maximally positive sentiment. Zero indicates neutral sentiment.

social.social_collection_timestamp
Type: String, ISO 8601 UTC datetime, nullable
Description: The timestamp at which the social data in this section was collected. Social data ages differently from market data, and this timestamp allows downstream components to assess the staleness of social signals independently of market data staleness.

social.trending_platforms
Type: Array of strings, nullable
Description: The list of platforms on which this token is currently trending. Values are platform identifier strings from the AHOS platform registry such as dexscreener_trending, coingecko_trending, twitter_trending. An empty array indicates the token is not trending on any monitored platform. Null indicates trending status has not been checked.

================================================================================
SECTION 13 — DISCOVERY SECTION
================================================================================

The discovery section records the context in which this token was discovered by the AHOS Discovery Engine. This section is populated at creation time and is not modified by enrichment stages. It represents the discovery state as it existed at the moment the token first entered the AHOS pipeline.

discovery.first_seen_timestamp
Type: String, ISO 8601 UTC datetime, non-null
Description: The timestamp at which this token was first observed by any AHOS collector across all collection runs and all sources. This is the canonical AHOS first-discovery timestamp. It is set only once and never updated, even if the token is subsequently seen in many more collection runs.

discovery.first_seen_source
Type: String, non-null
Description: The source_id of the source from which this token was first discovered. This records which data source gave AHOS its first sight of this token.

discovery.first_seen_collector
Type: String, non-null
Description: The collector_id of the AHOS collector that first discovered this token.

discovery.signal_set
Type: Array of signal objects, non-null
Description: The complete set of discovery signals triggered for this token at the time of first qualification. Each signal object contains: signal_id (string), signal_category (string: NEW_LAUNCH, RECENT_LAUNCH, TRENDING, ABNORMAL_VOLUME, ABNORMAL_LIQUIDITY, UNUSUAL_ATTENTION), signal_name (string), trigger_value (number representing the metric value that triggered the signal), threshold_value (number representing the configured threshold that was crossed), signal_weight (number representing the configured weight of this signal in the priority score), and triggered_at (ISO 8601 UTC string). An empty array indicates the token entered the pipeline without triggering any signals, which should only occur for watchlisted tokens.

discovery.priority_score
Type: Number, nullable, range 0.0 to 100.0
Description: The pre-AI priority score assigned by the Discovery Engine at qualification time. This score is calculated according to the Priority Scoring specification in the AHOS Phase 2 Architecture document and is not modified after initial assignment.

discovery.priority_band
Type: String, nullable
Description: The priority band classification corresponding to the priority score. Valid values: CRITICAL (85-100), HIGH (65-84), STANDARD (40-64), LOW (0-39). Populated at the same time as priority_score.

discovery.scoring_config_version
Type: String, nullable
Description: The version identifier of the scoring configuration used to calculate priority_score. This enables historical analysis of how score values change as scoring configuration evolves.

discovery.sources_observed
Type: Array of strings, non-null
Description: The list of source_id values from all sources in which this token has been observed as of the most recent collection run. This array grows as the token is seen across more sources. It is distinct from metadata.enrichment_history, which tracks enrichment operations. sources_observed tracks passive multi-source co-occurrence.

discovery.source_first_seen_timestamps
Type: Object, non-null
Description: A key-value map where each key is a source_id and each value is the ISO 8601 UTC timestamp at which this token was first observed in that source. This enables analysis of how quickly a token propagates across sources, which is itself a signal of attention velocity.

discovery.watchlisted
Type: Boolean, non-null
Description: True when this token entered the pipeline through the AHOS watchlist mechanism rather than through normal signal-based qualification. False in all other cases. Never null.

discovery.watchlist_added_by
Type: String, nullable
Description: The identifier of the operator or automated system that added this token to the watchlist. Null when watchlisted is false.

================================================================================
SECTION 14 — QUALITY SECTION
================================================================================

The quality section records the results of all data quality assessments performed on this UMO instance. Every data quality issue found during normalization, validation, or enrichment is recorded here rather than silently discarded. The quality section is the audit trail for data integrity decisions.

quality.is_valid
Type: Boolean, non-null
Description: The overall validity determination for this UMO instance. True when the instance has passed all mandatory validation rules defined in Section 17. False when one or more mandatory validation rules have failed. This field is set by the Normalization Module at creation time and is the primary signal consumed by downstream components for accept-or-reject routing decisions.

quality.validation_timestamp
Type: String, ISO 8601 UTC datetime, non-null
Description: The timestamp at which the quality validation producing the current is_valid determination was performed.

quality.validation_version
Type: String, non-null
Description: The version identifier of the validation rule set applied to produce the current quality assessment. Follows semantic versioning. Enables detection of quality assessment changes when validation rules are updated.

quality.issues
Type: Array of quality issue objects, non-null
Description: An ordered list of all data quality issues identified in this UMO instance. Each quality issue object contains: issue_id (string UUID), issue_code (string from the AHOS quality issue code registry), issue_severity (string: CRITICAL, ERROR, WARNING, INFO), field_path (dot-notation string identifying the affected field), source_value (string representation of the value that caused the issue), resolution (string describing how the issue was resolved: FIELD_SET_NULL, VALUE_TRUNCATED, VALUE_CONVERTED, PAIR_FLAGGED, PAIR_REJECTED), and detected_at (ISO 8601 UTC string). An empty array indicates a clean UMO instance with no identified quality issues.

quality.field_completeness_score
Type: Number, non-null, range 0.0 to 1.0
Description: The ratio of non-null optional fields to total optional fields in this UMO instance. A score of 1.0 indicates all optional fields are populated. A score of 0.0 indicates no optional fields are populated. This score is used by downstream components to prioritize fully-enriched UMO instances for time-sensitive analysis.

quality.required_fields_complete
Type: Boolean, non-null
Description: True when all required fields defined in Section 2 are non-null. False when any required field is null. When this field is false, quality.is_valid must also be false.

quality.source_trust_score
Type: Number, nullable, range 0.0 to 1.0
Description: A composite score reflecting the historical reliability of the data source that produced this UMO instance. Higher values indicate higher historical accuracy and consistency. This score is maintained by the AHOS source trust registry and is updated over time based on observed data quality from each source. It is attached to the UMO at normalization time from the registry lookup.

quality.flags
Type: Array of strings, non-null
Description: A list of named quality flag identifiers from the AHOS quality flag registry that apply to this UMO instance. Quality flags are distinct from quality issues: issues record specific data problems, flags record categorical quality characteristics. Example flag identifiers: SINGLE_SOURCE meaning only one source contributed data, PRICE_STALE meaning price data exceeds the freshness threshold, CHAIN_MISMATCH meaning the detected chain differs from the requested chain, ZERO_LIQUIDITY, ZERO_VOLUME, UNVERIFIED_CONTRACT. An empty array indicates no quality flags apply.

quality.price_freshness_seconds
Type: Integer, nullable, non-negative
Description: The age of the price data in this UMO instance in seconds, calculated as the difference between ingest_timestamp and the timestamp of the price observation as reported by the source. When the source does not provide a price observation timestamp, this field is null. Staleness thresholds are chain-and-source-specific and are defined in the AHOS configuration.

================================================================================
SECTION 15 — VERSIONING STRATEGY
================================================================================

The UMO versioning strategy governs how changes to the UMO standard are managed, communicated, and adopted across the AHOS platform.

15.1 Version Identifier Format

The UMO version identifier follows semantic versioning with three components: major, minor, and patch, expressed as a dot-separated string. The current version is 1.0.0.

Major version increments indicate breaking changes. A breaking change is any change that causes a UMO instance produced by the old version to fail validation against the new version's schema, or that changes the semantic meaning of an existing field. All consuming components must be updated before major version increments are deployed.

Minor version increments indicate backward-compatible additions. A minor version increment may add new optional fields to any section, add new values to any enumerated field's value set, or add new sections. UMO instances produced by a lower minor version remain valid under a higher minor version, with newly added fields absent rather than null in older instances. All consuming components must tolerate absent fields from older minor versions.

Patch version increments indicate non-structural clarifications. Patch increments may correct field descriptions, adjust validation rule thresholds, or add quality flag identifiers without changing the field set or field semantics. No consuming component changes are required for patch increments.

15.2 Version Field Placement

The umo_version field in the identity layer records the UMO standard version used to produce this specific instance. The schema_version field records the version of the internal schema definition file used for validation. These are two distinct fields because the UMO standard version and the implementing schema file version may differ during transition periods.

15.3 Version Registry

The AHOS platform maintains a UMO Version Registry that records: each released version, its release timestamp, the change log relative to the previous version, the minimum parser version required to produce instances conforming to that version, the minimum consuming component version required to process instances of that version, and the planned deprecation timestamp for older versions.

15.4 Multi-Version Coexistence

During major version transitions, the AHOS pipeline must support simultaneous processing of UMO instances conforming to two consecutive major versions. The consuming component is responsible for inspecting the umo_version field and applying the appropriate processing logic for that version. A maximum coexistence period of 90 days is defined: after 90 days from a major version release, support for the previous major version is deprecated and all producers must have migrated.

================================================================================
SECTION 16 — BACKWARD COMPATIBILITY STRATEGY
================================================================================

Backward compatibility is the guarantee that a consuming component built against UMO version N continues to function correctly when receiving UMO instances conforming to version N.x.y for any x and y greater than zero.

16.1 Field Addition Rules

New optional fields may be added in minor versions. Consuming components must treat any unrecognized field as ignorable. Consuming components must not fail on encountering unknown fields. This requires that all UMO deserializers be configured for lenient parsing that ignores unknown fields rather than strict parsing that fails on unknown fields.

16.2 Field Removal Rules

Fields may not be removed in minor versions. Fields may only be removed in major versions. Prior to removal in a major version, the field must be marked as deprecated in the UMO Version Registry for at least one full minor version cycle. Deprecated fields remain present in UMO instances but are populated with null and carry a deprecation notice in the quality section.

16.3 Field Semantic Preservation

The semantic meaning of any existing field must not change between minor versions. If a field's meaning must change, a new field with a distinct name must be introduced and the old field deprecated. This ensures that consuming components that were built against the field's original semantics continue to receive data matching those semantics.

16.4 Enumerated Value Expansion

New values may be added to enumerated fields such as risk.overall_risk_level or quality.issue_severity in minor versions. Consuming components must handle unknown enumeration values gracefully, typically by treating them as equivalent to the most conservative known value for risk fields or by logging a warning and continuing for non-risk fields.

16.5 Section Addition Rules

New top-level sections may be added in minor versions. Consuming components that do not process a new section ignore it without error. Components that do process a new section must check for the section's presence before accessing its fields because older UMO instances will not contain the new section.

================================================================================
SECTION 17 — MAPPING RULES
================================================================================

Mapping rules define how each known source's raw data fields are translated into UMO fields. These rules are implemented in source-specific parsers and must be version-controlled alongside the UMO standard itself.

17.1 Mapping Rule Principles

Every mapping rule must be deterministic. Given the same raw source value, the mapping rule must always produce the same UMO field value.

Every mapping rule must be defensive. If the source field is absent, null, of an unexpected type, or outside the expected range, the mapping rule must produce null for the UMO field rather than throwing an exception or producing a coerced value of uncertain accuracy.

Every mapping rule must be documented in the AHOS Parser Registry against the source and field it maps.

17.2 DexScreener Mapping Rules

DexScreener pair objects are the primary source for the following UMO fields with these specific mappings:

pair_address maps from pairAddress. Trimmed of whitespace. Validated against chain-specific address format.

chain_id maps from chainId. Stored as lowercase. Validated against the AHOS chain registry.

dex_id maps from dexId. Stored as lowercase.

token.address maps from baseToken.address. Format validated.

token.symbol maps from baseToken.symbol. Whitespace trimmed.

token.name maps from baseToken.name. Whitespace trimmed.

quote.address maps from quoteToken.address. Format validated.

quote.symbol maps from quoteToken.symbol.

price.usd maps from priceUsd. Parsed as float. Validated as non-negative finite number.

price.native maps from priceNative. Parsed as float when present.

price.change_5m maps from priceChange.m5. Parsed as float.

price.change_1h maps from priceChange.h1. Parsed as float.

price.change_6h maps from priceChange.h6. Parsed as float.

price.change_24h maps from priceChange.h24. Parsed as float.

liquidity.usd maps from liquidity.usd. Parsed as float. Validated as non-negative.

liquidity.base maps from liquidity.base. Parsed as float.

liquidity.quote maps from liquidity.quote. Parsed as float.

volume.m5 maps from volume.m5. Parsed as float.

volume.h1 maps from volume.h1. Parsed as float.

volume.h6 maps from volume.h6. Parsed as float.

volume.h24 maps from volume.h24. Parsed as float.

volume.buys_m5 maps from txns.m5.buys. Parsed as integer.

volume.sells_m5 maps from txns.m5.sells. Parsed as integer.

volume.buys_h1 maps from txns.h1.buys. Parsed as integer.

volume.sells_h1 maps from txns.h1.sells. Parsed as integer.

volume.buys_h24 maps from txns.h24.buys. Parsed as integer.

volume.sells_h24 maps from txns.h24.sells. Parsed as integer.

market.fdv maps from fdv. Parsed as float.

market.market_cap maps from marketCap. Parsed as float.

market.pair_created_at maps from pairCreatedAt. Parsed as Unix millisecond timestamp and converted to ISO 8601 UTC string.

17.3 GeckoTerminal Mapping Rules

GeckoTerminal uses a significantly different response structure with a data and attributes nesting pattern. Key mappings:

pair_address maps from data.id after extracting the address component from the compound identifier string.

chain_id maps from relationships.network.data.id.

token.address maps from relationships.base_token.data.id after chain prefix removal.

token.symbol maps from data.attributes.base_token_symbol.

price.usd maps from data.attributes.base_token_price_usd. Parsed as float.

liquidity.usd maps from data.attributes.reserve_in_usd. Parsed as float.

volume.h24 maps from data.attributes.volume_usd.h24. Parsed as float.

price.change_24h maps from data.attributes.price_change_percentage.h24.

market.pair_created_at maps from data.attributes.pool_created_at. Parsed from ISO 8601 string format.

17.4 Birdeye Mapping Rules

Birdeye provides Solana-focused data with some Solana-specific field conventions.

pair_address maps from address.

chain_id is derived from the collection job's chain field because Birdeye's response does not always include the chain identifier.

token.address maps from baseToken.address or base_mint depending on the specific Birdeye endpoint.

token.symbol maps from baseToken.symbol.

price.usd maps from price. Parsed as float.

liquidity.usd maps from liquidity. Parsed as float.

volume.h24 maps from volume24h or v24hUSD depending on endpoint version. Parser must attempt both field names in precedence order.

market.fdv maps from fdv. Parsed as float.

17.5 GMGN Mapping Rules

GMGN provides Solana-specific memecoin data with a focus on newly launched tokens.

pair_address maps from the pool address field in GMGN's response structure.

token.address maps from the token mint address.

token.symbol maps from symbol.

price.usd maps from price_usd. Parsed as float.

liquidity.usd maps from liquidity_usd. Parsed as float.

volume.h24 maps from volume_24h. Parsed as float.

market.pair_created_at maps from created_at. Format parsing attempts ISO 8601 first, Unix timestamp second.

17.6 Pump.fun Mapping Rules

Pump.fun provides data specific to tokens launched through its bonding curve mechanism. The bonding curve lifecycle introduces fields not present in traditional AMM pair data.

pair_address maps from the bonding curve account address, not a traditional AMM pool address. This distinction must be recorded in a Pump.fun-specific extension field within the discovery section.

token.address maps from mint.

token.symbol maps from symbol.

price.usd is derived from the bonding curve state: current price is calculated from the virtual SOL reserves and virtual token reserves using the bonding curve formula, then converted to USD using the current SOL/USD rate fetched from the AHOS rate oracle.

liquidity.usd is derived from the real SOL reserves in the bonding curve account, converted to USD.

market.pair_created_at maps from created_timestamp.

A Pump.fun-specific graduated flag is stored in the discovery section's extension object, indicating whether the token has graduated from the bonding curve to Raydium, because this graduation event is a primary discovery signal for Pump.fun-originated tokens.

17.7 Raydium and Jupiter Mapping Rules

Raydium and Jupiter are DEX protocol sources accessed directly rather than through aggregators. Their data arrives in protocol-specific formats requiring custom parsers. The field mappings follow the same patterns as DEX-class sources with source-specific field name variations documented in their respective parser specifications.

17.8 Field Authority in Multi-Source Instances

When a UMO instance is enriched by multiple sources and the sources provide conflicting values for the same UMO field, the field authority order determines which value is stored. The authority hierarchy is:

First authority: On-chain explorer sources for contract-level facts including token.decimals, token.is_verified, token.deployer_address, token.deploy_timestamp, and token.total_supply.

Second authority: DEX-class sources for real-time trading data including price.usd, price.native, price.change fields, liquidity.usd, liquidity.base, liquidity.quote, volume fields, and market.transactions_24h.

Third authority: Aggregator-class sources for market-wide metrics including market.market_cap, market.fdv, market.rank, token.circulating_supply, token.coingecko_id, and token.coinmarketcap_id.

Fourth authority: Social-class sources for all fields in the social section.

Fifth authority: Security-class sources for all fields in the risk section.

When two sources of the same authority class provide conflicting values, the most recently collected value takes precedence and the conflict is recorded in the quality section.

================================================================================
SECTION 18 — VALIDATION RULES
================================================================================

Validation rules define the constraints that every UMO instance must satisfy. Validation is performed at creation time and at each enrichment stage. The result of each validation pass is recorded in the quality section.

18.1 Identity Layer Validation

umo_id must be a UUID v4 format string. Validation fails if the format does not match.

umo_version must match the regex pattern for semantic versioning: integer dot integer dot integer. Validation fails for any other format.

pair_address must be a non-empty string conforming to the address format registered for the chain_id in the AHOS chain format registry. Validation fails if the address format does not match the chain-specific pattern.

chain_id must be a non-empty string present in the AHOS chain registry. Validation fails for unrecognized chain identifiers. The AHOS chain registry is the authoritative list of supported chains and is updated through the chain registration process defined separately.

collector_id must be a non-empty string present in the AHOS collector registry. Validation fails for unrecognized collector identifiers.

ingest_timestamp must be a valid ISO 8601 UTC datetime string. Validation fails for any other format. Additionally, ingest_timestamp must not be in the future. Timestamps more than 60 seconds in the future relative to the validation timestamp are flagged as a clock synchronization issue.

18.2 Token Section Validation

token.address must conform to the chain-specific address format derived from chain_id. For EVM chains, this is a 0x-prefixed 42-character string containing only valid hexadecimal characters. For Solana, this is a 32-to-44-character base58 string.

token.symbol must be between 1 and 32 characters inclusive. Symbols consisting entirely of whitespace fail validation after trimming.

token.decimals when present must be an integer in the range 0 to 18 inclusive. Non-integer values, negative values, and values exceeding 18 fail validation.

token.total_supply when present must be a non-negative finite number. Infinite values, NaN values, and negative values fail validation.

token.circulating_supply when present must not exceed token.total_supply when total_supply is also present. Violation of this relationship is a validation failure recorded in quality.issues with severity ERROR.

18.3 Price Section Validation

price.usd when present must be a non-negative finite number. Negative prices, infinite prices, and NaN values fail validation with severity CRITICAL.

When price.usd is null, price.usd_unavailable_reason must be present and must contain one of the defined enumerated values. A null price without an unavailable reason is a validation failure.

price.high_24h when present must be greater than or equal to price.low_24h when low_24h is also present. Violation causes both fields to be set to null with the violation recorded in quality.issues.

Price change fields such as price.change_5m, price.change_1h, price.change_6h, and price.change_24h when present must be finite numbers. There is no range constraint on price change percentages because extremely large changes are valid for newly launched tokens. However, values that would imply a price change of more than one million percent in either direction are flagged as potential data source errors in quality.flags without nullifying the field.

18.4 Liquidity Section Validation

liquidity.usd when present must be a non-negative finite number.

liquidity.base_usd when present plus liquidity.quote_usd when present must approximately equal liquidity.usd when all three are present. A tolerance of 5 percent is permitted to accommodate rounding differences between sources. Violations beyond this tolerance are recorded in quality.issues with severity WARNING.

18.5 Volume Section Validation

All volume amount fields must be non-negative finite numbers when present.

All volume count fields such as buys_h24 and sells_h24 must be non-negative integers when present.

volume.buy_sell_ratio_h24 must be a non-negative number when present. Values exceeding the configured maximum ratio sentinel value are capped at the sentinel and the cap is recorded in quality.flags.

18.6 Market Section Validation

market.pair_age_seconds must not be negative. A negative pair age implies the pair was created in the future, which is a clock synchronization or data source error. Negative pair ages are set to null and flagged.

market.pair_created_at when present must be a valid ISO 8601 UTC datetime string representing a time in the past. Future creation timestamps fail validation.

18.7 Cross-Section Validation

The chain_id in the identity layer must match the chain_id referenced in token.address format validation. When the address format is inconsistent with the declared chain, this is a CRITICAL quality issue.

The chain_requested field in metadata must match chain_id. A mismatch is an ERROR-severity quality issue recorded in quality.issues and the CHAIN_MISMATCH flag is set in quality.flags.

When risk.top_holder_pct and risk.top_10_holders_pct are both present, top_10_holders_pct must be greater than or equal to top_holder_pct. Violation is an ERROR-severity quality issue.

When price.ath is present, price.ath_timestamp must also be present. When price.ath_timestamp is present without price.ath, the timestamp is set to null and the issue is recorded.

================================================================================
SECTION 19 — NULL HANDLING RULES
================================================================================

Null handling in the UMO follows a strict semantic framework. Null values are never implicit. Every null value in a UMO instance has a defined meaning and the distinction between different null causes must be preservable through the data pipeline.

19.1 Null Semantics

Null in a UMO field means exactly one of the following: the source did not provide this data, the data could not be parsed from the source's response, the data failed validation and was set to null as a resolution, or the data applies only after enrichment and enrichment has not yet occurred. These causes are distinguished through the quality section rather than through separate null-reason fields, which would triple the field count unnecessarily.

19.2 Null vs. Zero

Zero and null are never interchangeable in the UMO. A liquidity.usd value of zero means the liquidity pool has zero liquidity. A null liquidity.usd means the liquidity is unknown. These are fundamentally different states with different implications for discovery signal rules. Any parser that produces zero for an unknown value rather than null is introducing a data integrity violation. All parsers must explicitly distinguish between a source providing the value zero and a source not providing a value.

19.3 Null vs. Absent

In the UMO's serialized forms, null and absent fields have different meanings. A field set to null is present in the serialized form with a null value, indicating the field was evaluated and found to have no value. An absent field is not present in the serialized form, indicating the field was not evaluated. In the UMO standard, fields that are part of the defined schema must always be present in UMO instances at the version that introduced them, even if their value is null. Absent fields indicate the UMO instance was produced by a parser conforming to an older version that did not include the field.

19.4 Null Propagation Rules

When a field's value depends on another field that is null, the dependent field must also be null rather than being calculated with a substitute value. For example, market.pair_age_seconds depends on market.pair_created_at. If market.pair_created_at is null, market.pair_age_seconds must be null rather than being calculated using a substitute creation time. Null propagation prevents the accumulation of derived errors from unknown inputs.

19.5 Null in Array Fields

Array fields such as discovery.signal_set and metadata.enrichment_history must never be null. They must be initialized as empty arrays. The semantic distinction between null and empty array in the UMO is: null means the field has not been populated, empty array means the field has been populated and the result is that there are zero elements. For fields that are defined as always-populated, null is not an acceptable substitute for an empty array.

19.6 Null in Nested Section Objects

Nested section objects such as the token, price, liquidity sections must never be null at the section level. If no data is available for any field within a section, the section object is present with all its fields set to null individually. A null section object is not acceptable because it prevents consuming components from inspecting individual field nullness without null-checking the parent first.

================================================================================
SECTION 20 — NAMING CONVENTIONS
================================================================================

20.1 Field Name Format

All UMO field names at every level of the hierarchy use snake_case exclusively. No camelCase, no PascalCase, no kebab-case, no ALL_CAPS. This convention applies without exception to ensure consistent access patterns across all AHOS components regardless of their implementation language.

20.2 Field Name Semantic Rules

Field names must be self-describing within the context of their containing section. A field named usd within the price section is acceptable because the section context makes the meaning clear. A field named p_usd at the top level would not be acceptable because the abbreviation requires external knowledge to interpret.

Boolean fields must use the is_ prefix for state conditions (is_valid, is_verified, is_mintable) and the has_ prefix for presence conditions (has_liquidity_lock, has_social_profile). Boolean fields must never use a name that is ambiguous between true and false directions. A field named unlocked is ambiguous. A field named is_locked is unambiguous.

Timestamp fields must use the _at suffix for event timestamps (created_at, updated_at, deployed_at) and the _timestamp suffix for process timestamps that represent when an AHOS operation was performed (collection_timestamp, validation_timestamp, normalization_timestamp). This distinction separates business-domain timestamps from system-operation timestamps.

Percentage fields must use the _pct suffix. Ratio fields must use the _ratio suffix. Score fields must use the _score suffix. Count fields must use the _count suffix when the count noun is not already part of the field name. Duration fields must use the _seconds, _ms, or _minutes suffix according to the unit.

20.3 Section Name Rules

Section names are singular nouns describing the domain of their contents. Sections are named: token, quote, market, price, liquidity, volume, risk, social, discovery, quality, metadata. Future sections must follow this singular noun convention.

20.4 Enumerated Value Format

All string-typed enumerated values use SCREAMING_SNAKE_CASE. Examples: CRITICAL, DATABASE_FAILURE, ABNORMAL_VOLUME, CHAIN_MISMATCH. This convention makes enumerated values visually distinct from free-text string values in UMO instance inspections.

20.5 Identifier Field Conventions

Fields that serve as identifiers, references, or keys end with the _id suffix when they identify an entity by a generated or registered identifier (umo_id, job_id, chain_id, collector_id), and with the _address suffix when they identify an entity by its on-chain address (pair_address, token.address, quote.address, token.deployer_address).

================================================================================
SECTION 21 — FUTURE EXTENSIBILITY
================================================================================

21.1 Extension Object Pattern

Each section of the UMO contains an implicit extension capability. When a new source provides data that is specific to that source and does not map to any existing UMO field, that data is stored in a source-specific extension object within the most relevant section. Extension objects follow the naming convention source_name_extensions where source_name is the lowercase source identifier. For example, Pump.fun-specific graduation state data is stored in a discovery.pump_fun_extensions object. Extension objects are always optional and are never accessed by platform-wide components. They are consumed only by source-specific downstream processors that understand the source's unique data model.

21.2 New Source Onboarding

Adding a new source to the AHOS platform requires: defining the source's collection profile in the AHOS source registry, implementing a parser that maps the source's fields to UMO fields according to the mapping rule principles in Section 17, documenting the mapping rules in the AHOS Parser Registry, defining the source's field authority level for each field it provides, and validating the parser against a representative set of the source's API responses. No changes to the UMO standard itself are required to add a new source unless the source provides genuinely novel data that requires new UMO fields, in which case a minor version increment is initiated.

21.3 New Section Onboarding

Adding a new section to the UMO is a minor version increment. The new section must be proposed with a complete field specification, a definition of which sources will populate it, a mapping rule specification for each initial source, and a validation rule specification. New sections must follow all naming conventions and null handling rules from their first version.

21.4 AI Feature Vector Compatibility

The UMO is designed to be the direct source for AI feature vector extraction in Phase 4. Every numeric field in the UMO is a potential feature. The field structure is organized to support systematic extraction of all numeric fields as a feature vector without requiring knowledge of the UMO's semantic structure by the extraction component. Future AI model iterations may require new features that necessitate new UMO fields. These additions follow the minor version process. Deprecated features that no longer contribute to model performance result in field deprecation through the standard deprecation process, not immediate removal.

21.5 Multi-Chain Evolution

The UMO is designed to support chains that do not yet exist at the time of this specification. The chain_id field combined with the AHOS chain format registry provides the extensibility point for new chains. Adding a new chain requires registering the chain's identifier and address format in the chain registry. No UMO structural changes are required unless the new chain introduces a fundamentally different asset model that requires new fields, such as a chain with multi-token pool assets or with native account-based token representations that differ from both EVM and Solana models.

21.6 Real-Time Streaming Compatibility

The UMO is currently designed for batch-collected snapshot data. Future AHOS versions may incorporate real-time streaming data from WebSocket feeds or push-based APIs. The UMO structure accommodates streaming by the addition of a streaming section in a future minor version that will carry: stream_sequence_number, stream_source_latency_ms, is_delta_update (distinguishing full snapshots from partial updates), and changed_fields (an array of dot-notation paths identifying which fields changed in a delta update). The existing snapshot semantics are fully preserved for non-streaming sources.

================================================================================
END OF DOCUMENT
AHOS Universal Market Object Standard v1.0
Official Architecture Standard
All AHOS engineering teams are bound by this specification.
Changes to this standard require a formal version increment review.
================================================================================