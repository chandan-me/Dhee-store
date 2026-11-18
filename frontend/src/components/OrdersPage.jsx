import React, { useState, useMemo } from "react";
import { formatCurrency, formatNumber } from "../utils/format";

/**
 * Dedicated "My Orders" / "Platform Orders" Page
 * - Bundles items purchased in the same checkout session into unified Order Cards
 * - Displays separate, random alphanumeric Order IDs (e.g. ORD-RX7IW5) for EVERY product stored in MySQL
 * - Provides live search bar to search by random Order ID, DB record number, Product Name, Product ID, Customer ID, or Payment ID
 * - Enables admin and customers to access any order by its number and view its full products list
 */
export default function OrdersPage({
  orders = [],
  products = [],
  isAdmin,
  onNavigateToProducts,
  onDeleteOrderRecord,
}) {
  // Search & Filtering State
  const [searchQuery, setSearchQuery] = useState("");
  const [paymentFilter, setPaymentFilter] = useState("ALL"); // "ALL" | "RAZORPAY" | "COD"

  // Group orders by checkout session (order_group_id / payment_id / individual order)
  const groupedOrders = useMemo(() => {
    const groups = new Map();

    orders.forEach((order) => {
      // Grouping key: order_group_id -> payment_id -> individual order ID
      const groupKey =
        order.order_group_id ||
        (order.payment_id && order.payment_id.trim() ? order.payment_id.trim() : null) ||
        order.order_number ||
        `ORD-${order.id}`;

      if (!groups.has(groupKey)) {
        groups.set(groupKey, {
          groupKey,
          userId: order.user_id,
          status: order.status || "COMPLETED",
          paymentMethod: order.payment_method || "COD",
          paymentId: order.payment_id || null,
          items: [],
          totalAmount: 0,
          totalQuantity: 0,
          orderIds: [],
          orderNumbers: [],
        });
      }

      const grp = groups.get(groupKey);
      grp.items.push(order);
      grp.totalAmount += Number(order.total_price || 0);
      grp.totalQuantity += Number(order.quantity || 1);
      grp.orderIds.push(order.id);
      if (order.order_number) {
        grp.orderNumbers.push(order.order_number);
      }
    });

    return Array.from(groups.values());
  }, [orders]);

  // Clean query strings for comparison
  const trimmedQuery = searchQuery.trim().toLowerCase();
  const cleanNumericQuery = trimmedQuery.replace(/^#/, "").trim();

  // Filter grouped orders based on search query and payment filter
  const filteredGroups = useMemo(() => {
    let result = groupedOrders;

    // Filter by payment method
    if (paymentFilter !== "ALL") {
      result = result.filter(
        (g) => (g.paymentMethod || "").toUpperCase() === paymentFilter.toUpperCase()
      );
    }

    if (!trimmedQuery) {
      return result;
    }

    return result.filter((group) => {
      // 1. Check if search query matches any item's random alphanumeric Order ID (e.g. ORD-RX7IW5) or numeric ID
      const matchesAnyOrderId = group.items.some((item) => {
        const orderNum = (item.order_number || "").toLowerCase();
        if (orderNum && orderNum.includes(trimmedQuery)) return true;
        const idStr = String(item.id);
        return idStr === cleanNumericQuery || idStr.includes(cleanNumericQuery);
      });
      if (matchesAnyOrderId) return true;

      // 2. Check groupKey (e.g. COD-7K2M9P, RZP-..., ORD-...)
      if (group.groupKey && group.groupKey.toLowerCase().includes(trimmedQuery)) {
        return true;
      }

      // 3. Check Customer ID
      if (String(group.userId) === cleanNumericQuery || `customer #${group.userId}`.includes(trimmedQuery)) {
        return true;
      }

      // 4. Check Payment ID or Method
      if (group.paymentId && group.paymentId.toLowerCase().includes(trimmedQuery)) {
        return true;
      }
      if (group.paymentMethod && group.paymentMethod.toLowerCase().includes(trimmedQuery)) {
        return true;
      }

      // 5. Check Status
      if (group.status && group.status.toLowerCase().includes(trimmedQuery)) {
        return true;
      }

      // 6. Check Products inside this order (Product Name, Product ID, Category)
      const matchesProduct = group.items.some((item) => {
        if (String(item.product_id) === cleanNumericQuery) {
          return true;
        }
        const prod = products.find((p) => p.id === item.product_id);
        if (prod) {
          if (prod.name && prod.name.toLowerCase().includes(trimmedQuery)) return true;
          if (prod.category && prod.category.toLowerCase().includes(trimmedQuery)) return true;
        }
        return false;
      });

      return matchesProduct;
    });
  }, [groupedOrders, paymentFilter, trimmedQuery, cleanNumericQuery, products]);

  // Helper: check if a specific item row matches current search query
  const isItemSearchMatched = (item, prodName) => {
    if (!trimmedQuery) return false;
    const orderNum = (item.order_number || `ORD-${item.id}`).toLowerCase();
    if (orderNum.includes(trimmedQuery)) return true;
    if (String(item.id) === cleanNumericQuery) return true;
    if (String(item.product_id) === cleanNumericQuery) return true;
    if (prodName.toLowerCase().includes(trimmedQuery)) return true;
    return false;
  };

  // Quick stats for filter chips
  const totalRazorpay = useMemo(
    () => groupedOrders.filter((g) => (g.paymentMethod || "").toUpperCase() === "RAZORPAY").length,
    [groupedOrders]
  );
  const totalCOD = useMemo(
    () => groupedOrders.filter((g) => (g.paymentMethod || "").toUpperCase() !== "RAZORPAY").length,
    [groupedOrders]
  );

  return (
    <div className="orders-page-container">
      {/* Page Header */}
      <div className="page-header-row">
        <div>
          <button
            type="button"
            className="secondary sm back-link-btn"
            onClick={onNavigateToProducts}
          >
            ← Back to Products
          </button>
          <h2 style={{ margin: "0.5rem 0 0 0" }}>
            {isAdmin ? "📦 Platform Orders Directory" : "📦 My Orders"}
          </h2>
          <p style={{ margin: "0.25rem 0 0 0", color: "#64748b", fontSize: "0.9rem" }}>
            {isAdmin
              ? "All customer transactions recorded across the distributed microservices. Each item holds a unique random alphanumeric Order ID in the database."
              : "Review your purchase history, fulfillment status, and separate alphanumeric item order IDs."}
          </p>
        </div>
      </div>

      {/* Interactive Search & Filter Toolbar */}
      {groupedOrders.length > 0 && (
        <div className="card orders-search-toolbar">
          <div className="orders-search-input-wrapper">
            <span className="orders-search-icon">🔍</span>
            <input
              type="text"
              className="orders-search-input"
              placeholder="Search by Order ID (e.g. ORD-RX7IW5 or #50), Product Name (e.g. Headphones), Product ID (#13), or Payment ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              aria-label="Search Orders"
            />
            {searchQuery && (
              <button
                type="button"
                className="orders-search-clear-btn"
                onClick={() => setSearchQuery("")}
                title="Clear Search Filter"
              >
                ✕
              </button>
            )}
          </div>

          <div className="orders-filter-chips-row">
            <div className="orders-filter-chips">
              <button
                type="button"
                className={`orders-filter-chip ${paymentFilter === "ALL" ? "active" : ""}`}
                onClick={() => setPaymentFilter("ALL")}
              >
                All Orders ({groupedOrders.length})
              </button>
              <button
                type="button"
                className={`orders-filter-chip ${paymentFilter === "RAZORPAY" ? "active" : ""}`}
                onClick={() => setPaymentFilter("RAZORPAY")}
              >
                ⚡ Razorpay ({totalRazorpay})
              </button>
              <button
                type="button"
                className={`orders-filter-chip ${paymentFilter === "COD" ? "active" : ""}`}
                onClick={() => setPaymentFilter("COD")}
              >
                💵 Cash on Delivery ({totalCOD})
              </button>
            </div>

            <div className="orders-search-meta">
              <span className="orders-counter-pill">
                Showing <strong>{filteredGroups.length}</strong> of <strong>{groupedOrders.length}</strong> {groupedOrders.length === 1 ? "order" : "orders"}
              </span>
              {(searchQuery || paymentFilter !== "ALL") && (
                <button
                  type="button"
                  className="orders-reset-btn"
                  onClick={() => {
                    setSearchQuery("");
                    setPaymentFilter("ALL");
                  }}
                >
                  ↺ Reset Filters
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {groupedOrders.length === 0 ? (
        <div className="card empty-page-card">
          <span style={{ fontSize: "3.5rem" }}>📭</span>
          <h3>No orders found</h3>
          <p style={{ color: "#64748b", maxWidth: "400px", margin: "0 auto 1.5rem auto" }}>
            You haven't placed any orders yet. Discover items in our store and complete a purchase!
          </p>
          <button
            type="button"
            className="product-card-cart-btn"
            style={{ width: "auto", display: "inline-flex", padding: "0.75rem 1.75rem" }}
            onClick={onNavigateToProducts}
          >
            🛍️ Browse Products
          </button>
        </div>
      ) : filteredGroups.length === 0 ? (
        <div className="card empty-page-card">
          <span style={{ fontSize: "3rem" }}>🔍</span>
          <h3>No matching orders found</h3>
          <p style={{ color: "#64748b", maxWidth: "440px", margin: "0 auto 1.25rem auto" }}>
            No orders match <strong>"{searchQuery}"</strong>
            {paymentFilter !== "ALL" ? ` with payment filter "${paymentFilter}"` : ""}.
            Try searching with an alphanumeric Order ID (e.g. <code>ORD-RX7IW5</code>), DB record (<code>#50</code>), a product name (e.g. <code>Backpack</code>), or clear the search.
          </p>
          <button
            type="button"
            className="secondary sm"
            onClick={() => {
              setSearchQuery("");
              setPaymentFilter("ALL");
            }}
          >
            ↺ Clear Search & Reset Filters
          </button>
        </div>
      ) : (
        <div className="orders-page-list">
          {filteredGroups.map((group) => {
            const hasMultipleItems = group.items.length > 1;
            // Display title: groupKey or first order number
            const firstItemOrderCode = group.items[0]?.order_number || `ORD-${group.items[0]?.id}`;
            const orderTitle = hasMultipleItems
              ? `Order Session: ${group.groupKey}`
              : `Order: ${firstItemOrderCode}`;

            return (
              <div key={group.groupKey} className="card order-bundle-card">
                {/* 1. Order Card Header */}
                <div className="order-bundle-header">
                  <div className="order-bundle-header-left">
                    <span className="order-id-badge">{orderTitle}</span>
                    {hasMultipleItems && (
                      <span className="order-bundle-badge">
                        🛍️ {group.items.length} Items in Order
                      </span>
                    )}
                    {isAdmin && (
                      <span
                        className="order-customer-tag clickable"
                        onClick={() => setSearchQuery(String(group.userId))}
                        title={`Click to filter orders by Customer #${group.userId}`}
                      >
                        👤 Customer ID: #{group.userId}
                      </span>
                    )}
                  </div>

                  <div className="order-bundle-header-right">
                    <span className={`status-badge ${group.status.toLowerCase()}`}>
                      {group.status}
                    </span>
                    {(group.paymentMethod || "").toUpperCase() === "RAZORPAY" ? (
                      <span className="order-payment-pill razorpay">
                        ⚡ Razorpay {group.paymentId ? `(#${group.paymentId.slice(-8)})` : ""}
                      </span>
                    ) : (
                      <span className="order-payment-pill cod">
                        💵 Cash on Delivery (COD)
                      </span>
                    )}
                  </div>
                </div>

                {/* Individual Alphanumeric Order IDs Strip for multi-product orders */}
                {hasMultipleItems && (
                  <div className="order-bundle-ids-strip">
                    <span className="order-bundle-ids-strip-label">
                      🏷️ Separate Item Order IDs:
                    </span>
                    <div className="order-bundle-ids-chips">
                      {group.items.map((it) => {
                        const code = it.order_number || `ORD-${it.id}`;
                        const isChipMatched = trimmedQuery && (code.toLowerCase().includes(trimmedQuery) || String(it.id) === cleanNumericQuery);
                        return (
                          <button
                            key={it.id}
                            type="button"
                            className={`order-id-chip-btn ${isChipMatched ? "active-chip" : ""}`}
                            onClick={() => setSearchQuery(code)}
                            title={`Filter to Order ID ${code}`}
                          >
                            {code}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* 2. Order Itemized Products List */}
                <div className="order-bundle-items-list">
                  {group.items.map((item) => {
                    const prod = products.find((p) => p.id === item.product_id);
                    const prodName = prod ? prod.name : `Product #${item.product_id}`;
                    const prodImage = prod?.image_url;
                    const unitPrice = Number(item.total_price) / item.quantity;
                    const isMatched = isItemSearchMatched(item, prodName);
                    const itemOrderCode = item.order_number || `ORD-${item.id}`;

                    return (
                      <div
                        key={item.id}
                        className={`order-bundle-item-row ${isMatched ? "matched-search-item" : ""}`}
                      >
                        {/* Thumbnail */}
                        <div className="order-item-thumb">
                          {prodImage ? (
                            <img
                              src={prodImage}
                              alt={prodName}
                              onError={(e) => {
                                e.target.style.display = "none";
                                if (e.target.nextSibling) {
                                  e.target.nextSibling.style.display = "flex";
                                }
                              }}
                            />
                          ) : null}
                          <span
                            className="order-thumb-placeholder"
                            style={{ display: prodImage ? "none" : "flex", fontSize: "1.4rem" }}
                          >
                            📦
                          </span>
                        </div>

                        {/* Title & Product Info with Separate Random Alphanumeric Order ID Badge */}
                        <div className="order-item-info">
                          <div className="order-item-title-row">
                            <span
                              className="order-item-id-pill"
                              onClick={() => setSearchQuery(itemOrderCode)}
                              title={`Click to filter by Order Code ${itemOrderCode}`}
                            >
                              🆔 Order ID: {itemOrderCode}
                            </span>
                            <h4 className="order-item-title">{prodName}</h4>
                            {isMatched && (
                              <span className="order-item-match-pill">
                                🎯 Matches Search
                              </span>
                            )}
                          </div>
                          <div className="order-item-meta">
                            <span
                              className="order-meta-prod-id clickable"
                              onClick={() => setSearchQuery(String(item.product_id))}
                              title={`Click to filter by Product #${item.product_id}`}
                            >
                              Product ID: #{item.product_id}
                            </span>
                            <span className="meta-dot">•</span>
                            <span>Unit Price: ₹{formatCurrency(unitPrice)}</span>
                            <span className="meta-dot">•</span>
                            <span className="order-meta-record-id">
                              DB Record: #{item.id}
                            </span>
                          </div>
                        </div>

                        {/* Quantity */}
                        <div className="order-item-qty">
                          <span className="qty-pill">
                            {formatNumber(item.quantity)} unit{item.quantity > 1 ? "s" : ""}
                          </span>
                        </div>

                        {/* Line Subtotal */}
                        <div className="order-item-subtotal">
                          ₹{formatCurrency(item.total_price)}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* 3. Order Card Footer & Totals */}
                <div className="order-bundle-footer">
                  <div className="order-bundle-footer-left">
                    <span className="order-fulfillment-badge">
                      ✅ {group.status === "COMPLETED" ? "Completed & Verified" : group.status}
                    </span>
                    <span className="order-total-units-text">
                      Total: <strong>{group.items.length} item{group.items.length > 1 ? "s" : ""}</strong> ({formatNumber(group.totalQuantity)} units)
                    </span>
                  </div>

                  <div className="order-bundle-footer-right">
                    <div className="order-grand-total">
                      <span className="total-label">Total Amount Paid:</span>
                      <span className="total-amount-val">
                        ₹{formatCurrency(group.totalAmount)}
                      </span>
                    </div>

                    {isAdmin && (
                      <button
                        type="button"
                        className="secondary-danger sm"
                        onClick={() => onDeleteOrderRecord(group.orderIds)}
                        title="Permanently delete this order record from database"
                      >
                        🗑️ Delete Record
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
