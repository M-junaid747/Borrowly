import React, { useLayoutEffect, useRef, useState } from "react";

/**
 * Sliding pill toggle between "Buying" and "Selling". If the user hasn't
 * enabled selling yet, choosing "Selling" here is what enables it
 * (see api.switchRole / SwitchRoleView on the backend).
 */
export default function RoleSwitch({ activeRole, onSwitch }) {
  const buyerRef = useRef(null);
  const sellerRef = useRef(null);
  const [thumbStyle, setThumbStyle] = useState({});

  useLayoutEffect(() => {
    const el = activeRole === "seller" ? sellerRef.current : buyerRef.current;
    if (el) {
      setThumbStyle({ left: el.offsetLeft, width: el.offsetWidth });
    }
  }, [activeRole]);

  return (
    <div className="role-switch">
      <span className="thumb" style={thumbStyle} />
      <button ref={buyerRef} className={activeRole === "buyer" ? "active" : ""} onClick={() => onSwitch("buyer")} type="button">
        Buying
      </button>
      <button ref={sellerRef} className={activeRole === "seller" ? "active" : ""} onClick={() => onSwitch("seller")} type="button">
        Selling
      </button>
    </div>
  );
}
