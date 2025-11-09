/**
 * T-Mobile Protocols, Policies, and Features
 * NOTE: These are example/placeholder policies for a demo.
 * Replace/validate with official T-Mobile documentation before production use.
 */

export const tmobilePolicies = {
    // Billing Policies
    billing: {
      payment_plans: [
        "FlexPay: Short-term payment arrangements available for eligible accounts (set up before due date).",
        "AutoPay discount: $5/month per eligible line when using a debit card or bank account.",
        "Split payments: May be available via the T-Mobile app or Care prior to due date.",
        "Paperless billing: Digital statements available; paper statements may incur a monthly fee."
      ],
      refund_policies: [
        "Service credit consideration for verified service interruptions/outages.",
        "Refunds/credits typically appear within 3–5 business days once approved.",
        "Prorated bill adjustments may apply when plans/features change mid-cycle.",
        "Refunds generally return to the original payment method after approval."
      ],
      late_fees: [
        "Grace period may apply after bill due date; late fees may apply afterward.",
        "Late fees can be waived on first occurrence at agent discretion (case by case).",
        "Customers on approved payment arrangements are not charged additional late fees during the arrangement window."
      ],
      promotions_and_discounts: [
        "Promotional bill credits begin within 1–2 bill cycles after qualification.",
        "All promotional credits require active service for the promo term.",
        "Stacking promos is limited; follow offer terms for eligibility."
      ],
    },
  
    // Network & Coverage Policies
    network: {
      coverage_guarantee: [
        "Network experience may vary by location, device, and conditions; check coverage map for current expected service.",
        "Wi-Fi Calling recommended in locations with weak indoor signal when available.",
        "Customers may request a signal-assist solution when persistent low indoor coverage is verified (where available)."
      ],
      network_optimization: [
        "Basic steps: Restart device, toggle Airplane Mode, check for OS/carrier updates, reseat/reprovision SIM/eSIM.",
        "Preferred network settings: Ensure 5G/VoLTE is enabled on compatible devices.",
        "Report issues via the T-Mobile app network feedback to aid troubleshooting."
      ],
      service_interruptions: [
        "Major outages are investigated; engineering tickets created for persistent or clustered incidents.",
        "Bill credits may be considered for verified outages exceeding a reasonable duration.",
        "Customers can receive status updates and ETAs when available for known incidents."
      ],
      roaming: [
        "Domestic roaming available at no extra cost in supported areas (usage policies apply).",
        "International data: plans may include basic speeds; high-speed passes available in many countries.",
        "Wi-Fi Calling can reduce international voice charges when calling over Wi-Fi to U.S. numbers."
      ],
    },
  
    // Device & Technical Support
    devices: {
      warranty: [
        "Manufacturer limited warranty typically 1 year for hardware defects (model-specific).",
        "Protection options may cover loss, theft, accidental damage, and defects (deductibles/limits apply).",
        "Device replacement/repair subject to coverage type, deductibles, and claim limits."
      ],
      upgrades: [
        "Upgrade eligibility depends on plan, device financing status, and promotions in effect.",
        "Trade-in credits depend on model and condition upon inspection.",
        "Promotional upgrade credits generally apply over monthly bill credits during the promo term."
      ],
      activation_and_esim: [
        "eSIM supported on compatible devices; remove line from old device before transferring to avoid activation failures.",
        "SIM/eSIM reprovisioning and carrier settings updates can resolve registration issues.",
        "Unlock eligibility depends on account tenure and device financing status; see unlock policy."
      ],
      troubleshooting: [
        "Standard steps: power cycle, network reset, APN/IMS re-provision, VoLTE/VoNR toggle on supported devices.",
        "Visual Voicemail: clear cache/data, profile refresh, and network toggle steps.",
        "Escalate persistent issues with logs, device model/OS, timestamp, and cell/Wi-Fi context."
      ],
    },
  
    // Account Management
    account: {
      plan_changes: [
        "Plan changes can apply immediately or at next cycle per customer choice (where supported).",
        "Most plans are no-contract; customers can change plans subject to offer terms.",
        "Multi-line/Family options available; line limits vary by account type and credit status."
      ],
      add_ons: [
        "Data passes/boosters available one-time or recurring depending on plan and availability.",
        "International add-ons: high-speed data and calling options vary by country.",
        "Select plans include streaming benefits; terms and eligibility vary."
      ],
      account_security: [
        "Account PIN/passcode required for sensitive changes; 2FA recommended.",
        "SIM-swap protections available; enable account-level security features.",
        "Secure channels (app/web) preferred for account management to protect PII."
      ],
    },
  
    // Customer Service Protocols
    service: {
      escalation: [
        "Tier 1: General Care handles billing/basic troubleshooting.",
        "Tier 2: Technical specialists for device/network deeper diagnostics.",
        "Engineering/NOC review for verified persistent/clustered network issues.",
        "Retention team engaged for cancellation/port-out risks."
      ],
      response_times: [
        "Phone support available 24/7; live chat availability may vary by channel.",
        "Target initial response within minutes via chat/social during business hours.",
        "Complex tickets receive case follow-ups with status updates when available."
      ],
      customer_satisfaction: [
        "Follow-ups and surveys may be sent after resolution.",
        "Service recovery can include courtesy credits consistent with policy.",
        "Document root cause and next steps for repeat-prevention."
      ],
    },
  
    // Retention & Cancellation
    retention: {
      cancellation_procedures: [
        "Attempt resolution first: identify root cause and propose solutions.",
        "If cancel requested, review remaining device balances/return obligations.",
        "Number portability requires active line and correct account/PIN info.",
        "Offer final invoice timeline and reactivation/number hold windows if applicable."
      ],
      retention_offers: [
        "Plan review: propose right-sized plan or feature changes that address pain points.",
        "Courtesy credits or temporary discounts may be considered per policy and eligibility.",
        "Device/coverage fixes prioritized before recurring credits; set clear expectations."
      ],
      win_back: [
        "Recently canceled lines may be eligible for reactivation within a limited window.",
        "Win-back promotions may be available; verify current eligibility and terms.",
        "Prior account history can help expedite setup if returning within the retention window."
      ],
    },
  
    // Promotions & Offers
    promotions: {
      new_customer: [
        "Port-in offers may include bill credits or device promos (proof/eligibility required).",
        "Add-a-line discounts for multi-line accounts; see active campaign terms.",
        "Limited-time deals rotate; verify stackability and start/end dates."
      ],
      existing_customer: [
        "Loyalty offers may apply based on tenure and account standing.",
        "Trade-in upgrade promos for select models; credits over time after validation.",
        "Feature bundles (e.g., streaming) may be included with eligible plans."
      ],
      seasonal: [
        "Holiday/back-to-school events often include device and plan promos.",
        "Referral programs may provide account credits upon validation.",
        "Campaign terms govern eligibility, stacking, and credit timing."
      ],
    },
  
    // Compliance & Legal
    compliance: {
      privacy: [
        "Customer data handled under applicable privacy laws (e.g., CCPA/GDPR equivalents where applicable).",
        "Customers can manage marketing preferences and certain data uses via privacy settings.",
        "Call recordings used for training/quality; retention and access policies apply."
      ],
      accessibility: [
        "Accessibility support offerings include TTY/TDD and relay services.",
        "Alternative statement formats (large print/braille) available on request.",
        "Reasonable accommodations are provided consistent with policy and law."
      ],
      dispute_resolution: [
        "Billing disputes typically must be raised within a specified window of the statement date.",
        "Arbitration/mediation options may be available; see terms for details.",
        "Regulatory complaint channels (e.g., state PUC/FCC equivalents) are available if unresolved."
      ],
    },
  };
  
  /**
   * Internal helpers
   */
  const uniq = (arr) => [...new Set(arr)];
  
  // Keyword → category routing map (used when explicit category is absent)
  const KEYWORD_MAP = {
    billing: ["bill", "billing", "charge", "payment", "refund", "credit", "autopay", "invoice"],
    network: ["coverage", "signal", "network", "connection", "outage", "roaming", "5g", "lte", "vonr"],
    device: ["phone", "device", "handset", "upgrade", "trade-in", "warranty", "esim", "sim"],
    cancellation: ["cancel", "switch", "port", "leave", "terminate", "move"],
    account: ["plan", "feature", "add-on", "family", "account", "security", "pin"],
    promotions: ["promo", "promotion", "discount", "offer", "deal", "credit"],
    compliance: ["privacy", "data", "gdpr", "ccpa", "accessibility", "tty", "braille", "dispute"],
  };
  
  /**
   * Get relevant policies based on context
   * @param {Object} context
   * @param {('billing'|'network'|'device'|'cancellation'|'account'|'promotions'|'compliance'|string)=} context.category
   * @param {string[]=} context.keywords
   * @param {('LOW'|'MEDIUM'|'HIGH')=} context.urgency
   * @param {number=} limit max number of policies to return (default 12)
   */
  export const getRelevantPolicies = (context = {}, limit = 12) => {
    const { category, keywords = [], urgency } = context;
    const kws = keywords.map((k) => String(k || "").toLowerCase());
    const out = [];
  
    // Resolve category candidates
    const cats = new Set();
    if (category && tmobilePolicies[category]) cats.add(category);
    // Derive from keywords if no/extra categories
    Object.entries(KEYWORD_MAP).forEach(([cat, keys]) => {
      if (kws.some((k) => keys.includes(k))) cats.add(cat);
    });
  
    // Gather from matched categories
    const addCategory = (cat, subs = []) => {
      const node = tmobilePolicies[cat];
      if (!node) return;
      const subkeys = subs.length ? subs : Object.keys(node);
      subkeys.forEach((sk) => {
        const arr = node[sk];
        if (Array.isArray(arr)) out.push(...arr);
      });
    };
  
    // Priority pulls by likely intent
    if (cats.has("billing")) addCategory("billing", ["payment_plans", "refund_policies", "late_fees", "promotions_and_discounts"]);
    if (cats.has("network")) addCategory("network", ["coverage_guarantee", "network_optimization", "service_interruptions", "roaming"]);
    if (cats.has("device")) addCategory("devices", ["activation_and_esim", "troubleshooting", "warranty", "upgrades"]);
    if (cats.has("cancellation")) addCategory("retention", ["cancellation_procedures", "retention_offers", "win_back"]);
    if (cats.has("account")) addCategory("account");
    if (cats.has("promotions")) addCategory("promotions");
    if (cats.has("compliance")) addCategory("compliance");
    // Fallback if nothing matched
    if (!out.length) addCategory("service"); // general support/escalation
  
    // Urgency hint: include escalation protocols when high urgency
    if (urgency === "HIGH") {
      out.push(...(tmobilePolicies.service?.escalation || []));
    }
  
    // Dedup and cap
    return uniq(out).slice(0, limit);
  };
  
  /**
   * Get specific policy text for a given topic (substring match, case-insensitive)
   * @param {string} topic
   * @returns {string|null}
   */
  export const getPolicyText = (topic) => {
    if (!topic) return null;
    const q = String(topic).toLowerCase();
  
    for (const category in tmobilePolicies) {
      const catNode = tmobilePolicies[category];
      for (const subcategory in catNode) {
        const policies = catNode[subcategory];
        if (!Array.isArray(policies)) continue;
        for (const policy of policies) {
          if (String(policy).toLowerCase().includes(q)) {
            return policy;
          }
        }
      }
    }
    return null;
  };
  
  export default tmobilePolicies;
  