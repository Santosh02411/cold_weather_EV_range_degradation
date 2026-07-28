import React, { useEffect, useState } from "react";
import { fetchPublicTracking } from "../services/api";
import { useTheme } from "../context/ThemeContext";
import StatusBadge from "./StatusBadge";

const STATUS_LABELS = {
  picked_up: "Picked Up",
  out_for_delivery: "Out for Delivery",
  delivered: "Delivered",
  failed_attempt: "Failed Attempt",
};

export default function TrackingPage({ deliveryId }) {
  const { theme, toggleTheme } = useTheme();
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPublicTracking(deliveryId)
      .then(setData)
      .catch((err) => setError(err.message));
  }, [deliveryId]);

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-page)", padding: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", maxWidth: "480px", margin: "0 auto 20px" }}>
        <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, color: "var(--accent)" }}>
          Delivery Sync — Tracking
        </span>
        <button className="btn" onClick={toggleTheme}>
          {theme === "dark" ? "☀" : "☾"}
        </button>
      </div>

      <div className="card" style={{ maxWidth: "480px", margin: "0 auto" }}>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}

        {!error && !data && <p style={{ color: "var(--text-secondary)" }}>Loading...</p>}

        {data && (
          <>
            <h2 className="mono" style={{ marginBottom: "8px" }}>{data.order_id}</h2>
            <StatusBadge status={data.status} />

            <div style={{ marginTop: "16px", display: "flex", flexDirection: "column", gap: "8px" }}>
              {data.zone && (
                <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>Zone: {data.zone}</div>
              )}
              {data.expected_by && (
                <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                  Expected by: {new Date(data.expected_by).toLocaleString()}
                </div>
              )}
              <div style={{ fontSize: "13px", color: "var(--text-secondary)" }}>
                Last updated: {new Date(data.updated_at).toLocaleString()}
              </div>
            </div>

            {data.proof_of_delivery && (
              <div style={{ marginTop: "16px" }}>
                <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginBottom: "6px" }}>
                  Proof of Delivery
                </div>
                <img
                  src={data.proof_of_delivery}
                  alt="Proof of delivery"
                  style={{ maxWidth: "100%", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-color)" }}
                />
              </div>
            )}

            <hr style={{ margin: "20px 0", border: "none", borderTop: "1px solid var(--border-color)" }} />

            <div style={{ fontSize: "13px", fontWeight: 600, marginBottom: "10px" }}>Timeline</div>
            {data.history.map((entry, i) => (
              <div key={i} style={{ borderLeft: "3px solid var(--accent)", paddingLeft: "10px", marginBottom: "10px" }}>
                <div style={{ fontSize: "13px", fontWeight: 600 }}>
                  {entry.old_status
                    ? `${STATUS_LABELS[entry.old_status] || entry.old_status} → ${STATUS_LABELS[entry.new_status] || entry.new_status}`
                    : `Order created (${STATUS_LABELS[entry.new_status] || entry.new_status})`}
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-secondary)" }}>
                  {new Date(entry.changed_at).toLocaleString()}
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
