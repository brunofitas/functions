# functions_shared

The contract spine. Defines the function/pipeline **manifest schema**, the
inputs/outputs/events contract, and the **runtime-adapter interface** — consumed by both
`functions_be` and `functions_fe`. Zero internal dependencies.

Contract: [`docs/decisions/d_001_function_contract.md`](../../docs/decisions/d_001_function_contract.md).
Implementation lands in story `shared_003`.
