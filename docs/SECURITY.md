# Security Notes

Implemented / intended controls:

1. Password hashing with bcrypt
2. Household-scoped authorization
3. HTTP-only auth cookies (+ Bearer for API clients)
4. Rate limiting hooks via Redis
5. File type/size validation
6. Pluggable malware scan interface
7. Backend-only LLM calls with masked samples
8. No raw PANs in logs
9. Audit events for mutations
10. Household export and deletion endpoints

Not claimed: PCI, SOC2, or other formal compliance certifications.
