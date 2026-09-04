import { jsxs as he, Fragment as Ce, jsx as ze } from "react/jsx-runtime";
import { forwardRef as Ge, useId as Me, useRef as Ie, useState as P, useEffect as B, useCallback as ye, useMemo as ve } from "react";
const Le = {
  sm: {
    borderRadius: 32,
    borderWidth: 1,
    width: 70,
    height: 36
  },
  md: {
    borderRadius: 16,
    borderWidth: 1
  },
  line: {
    borderRadius: 16,
    borderWidth: 1
  },
  "pulse-outside": {
    borderRadius: 16,
    borderWidth: 1
  },
  "pulse-inner": {
    borderRadius: 16,
    borderWidth: 1
  }
}, ne = {
  sm: {
    dark: {
      strokeOpacity: 0.46,
      innerOpacity: 0.24,
      bloomOpacity: 0.38,
      innerShadow: "rgba(255, 255, 255, 0.3)",
      saturation: 1.2
    },
    light: {
      strokeOpacity: 0.12,
      innerOpacity: 0.3,
      bloomOpacity: 0.16,
      innerShadow: "rgba(0, 0, 0, 0.14)",
      saturation: 1.8
    }
  },
  md: {
    dark: {
      strokeOpacity: 0.26,
      innerOpacity: 0.42,
      bloomOpacity: 0.24,
      innerShadow: "rgba(255, 255, 255, 0.27)",
      saturation: 1.2
    },
    light: {
      strokeOpacity: 0.12,
      innerOpacity: 0.26,
      bloomOpacity: 0.34,
      innerShadow: "rgba(0, 0, 0, 0.14)",
      saturation: 1.5
    }
  },
  line: {
    dark: {
      strokeOpacity: 1.14,
      innerOpacity: 0.7,
      bloomOpacity: 0.8,
      innerShadow: "rgba(255, 255, 255, 0.1)",
      saturation: 1.2
    },
    light: {
      strokeOpacity: 0.16,
      innerOpacity: 0.32,
      bloomOpacity: 0.3,
      innerShadow: "rgba(0, 0, 0, 0.14)",
      saturation: 1.95
    }
  },
  // Pulse Outside — outward-blooming breathe (ported from v5 "Breathe Outside Uncropped" / c6)
  "pulse-outside": {
    dark: {
      strokeOpacity: 0.94,
      innerOpacity: 0.34,
      bloomOpacity: 0.3,
      innerShadow: "transparent",
      saturation: 1.2,
      brightness: 1.9,
      // v5 Card 5 frames the card with a single 1px hairline (its box-shadow at
      // 0.3). Wrapped components here already supply their own ~equivalent 1px
      // border, so the beam must NOT add a second hairline on top or the edge
      // reads brighter than v5. Kept at 0 to match v5's single-hairline look.
      hairlineOpacity: 0
    },
    light: {
      strokeOpacity: 1.96,
      innerOpacity: 1.04,
      bloomOpacity: 0.42,
      innerShadow: "transparent",
      saturation: 0.6,
      brightness: 1.7,
      hairlineOpacity: 0
    }
  },
  // Pulse Inner — contained breathe (ported from v5 "Breathe" / c4)
  "pulse-inner": {
    dark: {
      strokeOpacity: 1.54,
      innerOpacity: 0.44,
      bloomOpacity: 0.66,
      innerShadow: "transparent",
      saturation: 1.2,
      brightness: 0.75
    },
    light: {
      strokeOpacity: 0.32,
      innerOpacity: 0.4,
      bloomOpacity: 0.8,
      innerShadow: "transparent",
      saturation: 0.75,
      brightness: 1.3
    }
  }
}, ha = {
  dark: { ...ne.md.dark },
  light: { ...ne.md.light }
}, C = {
  colorful: {
    border: [
      { color: "rgb(255, 50, 100)", pos: "33% -7.4%", size: "70px 40px" },
      { color: "rgb(40, 140, 255)", pos: "12% -5%", size: "60px 35px" },
      { color: "rgb(50, 200, 80)", pos: "2.1% 68.3%", size: "40px 70px" },
      { color: "rgb(30, 185, 170)", pos: "2.1% 68.3%", size: "20px 35px" },
      { color: "rgb(100, 70, 255)", pos: "74.4% 100%", size: "180px 32px" },
      { color: "rgb(40, 140, 255)", pos: "55% 100%", size: "85px 26px" },
      { color: "rgb(255, 120, 40)", pos: "93.9% 0%", size: "74px 32px" },
      { color: "rgb(240, 50, 180)", pos: "100% 27.1%", size: "26px 42px" },
      { color: "rgb(180, 40, 240)", pos: "100% 27.1%", size: "52px 48px" }
    ],
    spike: { primary: "rgb(255, 60, 80)", secondary: "rgba(40, 190, 180, 0.98)" },
    spikeLt: { primary: "rgb(200, 30, 60)", secondary: "rgb(20, 150, 140)" }
  },
  mono: {
    border: [
      { color: "rgb(180, 180, 180)", pos: "33% -7.4%", size: "70px 40px" },
      { color: "rgb(140, 140, 140)", pos: "12% -5%", size: "60px 35px" },
      { color: "rgb(160, 160, 160)", pos: "2.1% 68.3%", size: "40px 70px" },
      { color: "rgb(130, 130, 130)", pos: "2.1% 68.3%", size: "20px 35px" },
      { color: "rgb(170, 170, 170)", pos: "74.4% 100%", size: "180px 32px" },
      { color: "rgb(150, 150, 150)", pos: "55% 100%", size: "85px 26px" },
      { color: "rgb(190, 190, 190)", pos: "93.9% 0%", size: "74px 32px" },
      { color: "rgb(145, 145, 145)", pos: "100% 27.1%", size: "26px 42px" },
      { color: "rgb(165, 165, 165)", pos: "100% 27.1%", size: "52px 48px" }
    ],
    spike: { primary: "rgb(200, 200, 200)", secondary: "rgb(170, 170, 170)" },
    spikeLt: { primary: "rgb(80, 80, 80)", secondary: "rgb(120, 120, 120)" }
  },
  ocean: {
    border: [
      { color: "rgb(100, 80, 220)", pos: "33% -7.4%", size: "70px 40px" },
      { color: "rgb(60, 120, 255)", pos: "12% -5%", size: "60px 35px" },
      { color: "rgb(80, 100, 200)", pos: "2.1% 68.3%", size: "40px 70px" },
      { color: "rgb(50, 140, 220)", pos: "2.1% 68.3%", size: "20px 35px" },
      { color: "rgb(120, 80, 255)", pos: "74.4% 100%", size: "180px 32px" },
      { color: "rgb(70, 130, 255)", pos: "55% 100%", size: "85px 26px" },
      { color: "rgb(140, 100, 240)", pos: "93.9% 0%", size: "74px 32px" },
      { color: "rgb(90, 110, 230)", pos: "100% 27.1%", size: "26px 42px" },
      { color: "rgb(130, 70, 255)", pos: "100% 27.1%", size: "52px 48px" }
    ],
    spike: { primary: "rgb(100, 120, 255)", secondary: "rgba(130, 100, 220, 0.98)" },
    spikeLt: { primary: "rgb(60, 60, 180)", secondary: "rgb(80, 100, 200)" }
  },
  sunset: {
    border: [
      { color: "rgb(255, 80, 50)", pos: "33% -7.4%", size: "70px 40px" },
      { color: "rgb(255, 160, 40)", pos: "12% -5%", size: "60px 35px" },
      { color: "rgb(255, 120, 60)", pos: "2.1% 68.3%", size: "40px 70px" },
      { color: "rgb(255, 200, 50)", pos: "2.1% 68.3%", size: "20px 35px" },
      { color: "rgb(255, 100, 80)", pos: "74.4% 100%", size: "180px 32px" },
      { color: "rgb(255, 180, 60)", pos: "55% 100%", size: "85px 26px" },
      { color: "rgb(255, 60, 60)", pos: "93.9% 0%", size: "74px 32px" },
      { color: "rgb(255, 140, 50)", pos: "100% 27.1%", size: "26px 42px" },
      { color: "rgb(255, 90, 70)", pos: "100% 27.1%", size: "52px 48px" }
    ],
    spike: { primary: "rgb(255, 140, 80)", secondary: "rgba(255, 100, 60, 0.98)" },
    spikeLt: { primary: "rgb(200, 80, 40)", secondary: "rgb(220, 120, 30)" }
  }
}, He = {
  colorful: {
    border: [
      { color: "rgb(50, 200, 80)", pos: "2% 68%", size: "9px 18px" },
      { color: "rgb(30, 185, 170)", pos: "2% 68%", size: "4px 8px" },
      { color: "rgb(255, 120, 40)", pos: "72% -3%", size: "59px 9px" },
      { color: "rgb(100, 70, 255)", pos: "74% 100%", size: "42px 7px" },
      { color: "rgb(240, 50, 180)", pos: "100% 27%", size: "10px 17px" },
      { color: "rgb(180, 40, 240)", pos: "100% 27%", size: "10px 18px" },
      { color: "rgb(40, 140, 255)", pos: "100% 27%", size: "5px 10px" },
      { color: "rgb(255, 50, 100)", pos: "100% 27%", size: "11px 12px" }
    ],
    inner: [
      { color: "rgba(50, 200, 80, 0.5)", pos: "2% 68%", size: "9px 18px" },
      { color: "rgba(30, 185, 170, 0.45)", pos: "2% 68%", size: "4px 8px" },
      { color: "rgba(255, 120, 40, 0.35)", pos: "72% -3%", size: "59px 9px" },
      { color: "rgba(100, 70, 255, 0.35)", pos: "74% 100%", size: "42px 7px" },
      { color: "rgba(240, 50, 180, 0.3)", pos: "100% 27%", size: "10px 17px" },
      { color: "rgba(180, 40, 240, 0.4)", pos: "100% 27%", size: "10px 18px" },
      { color: "rgba(40, 140, 255, 0.3)", pos: "100% 27%", size: "5px 10px" },
      { color: "rgba(255, 50, 100, 0.3)", pos: "100% 27%", size: "11px 12px" }
    ]
  },
  mono: {
    border: [
      { color: "rgb(160, 160, 160)", pos: "2% 68%", size: "9px 18px" },
      { color: "rgb(140, 140, 140)", pos: "2% 68%", size: "4px 8px" },
      { color: "rgb(180, 180, 180)", pos: "72% -3%", size: "59px 9px" },
      { color: "rgb(150, 150, 150)", pos: "74% 100%", size: "42px 7px" },
      { color: "rgb(170, 170, 170)", pos: "100% 27%", size: "10px 17px" },
      { color: "rgb(155, 155, 155)", pos: "100% 27%", size: "10px 18px" },
      { color: "rgb(145, 145, 145)", pos: "100% 27%", size: "5px 10px" },
      { color: "rgb(165, 165, 165)", pos: "100% 27%", size: "11px 12px" }
    ],
    inner: [
      { color: "rgba(160, 160, 160, 0.25)", pos: "2% 68%", size: "9px 18px" },
      { color: "rgba(140, 140, 140, 0.22)", pos: "2% 68%", size: "4px 8px" },
      { color: "rgba(180, 180, 180, 0.17)", pos: "72% -3%", size: "59px 9px" },
      { color: "rgba(150, 150, 150, 0.17)", pos: "74% 100%", size: "42px 7px" },
      { color: "rgba(170, 170, 170, 0.15)", pos: "100% 27%", size: "10px 17px" },
      { color: "rgba(155, 155, 155, 0.20)", pos: "100% 27%", size: "10px 18px" },
      { color: "rgba(145, 145, 145, 0.15)", pos: "100% 27%", size: "5px 10px" },
      { color: "rgba(165, 165, 165, 0.15)", pos: "100% 27%", size: "11px 12px" }
    ]
  },
  ocean: {
    border: [
      { color: "rgb(60, 140, 200)", pos: "2% 68%", size: "9px 18px" },
      { color: "rgb(50, 120, 180)", pos: "2% 68%", size: "4px 8px" },
      { color: "rgb(100, 80, 220)", pos: "72% -3%", size: "59px 9px" },
      { color: "rgb(80, 100, 255)", pos: "74% 100%", size: "42px 7px" },
      { color: "rgb(120, 70, 240)", pos: "100% 27%", size: "10px 17px" },
      { color: "rgb(90, 80, 220)", pos: "100% 27%", size: "10px 18px" },
      { color: "rgb(70, 110, 255)", pos: "100% 27%", size: "5px 10px" },
      { color: "rgb(110, 90, 230)", pos: "100% 27%", size: "11px 12px" }
    ],
    inner: [
      { color: "rgba(60, 140, 200, 0.5)", pos: "2% 68%", size: "9px 18px" },
      { color: "rgba(50, 120, 180, 0.45)", pos: "2% 68%", size: "4px 8px" },
      { color: "rgba(100, 80, 220, 0.35)", pos: "72% -3%", size: "59px 9px" },
      { color: "rgba(80, 100, 255, 0.35)", pos: "74% 100%", size: "42px 7px" },
      { color: "rgba(120, 70, 240, 0.3)", pos: "100% 27%", size: "10px 17px" },
      { color: "rgba(90, 80, 220, 0.4)", pos: "100% 27%", size: "10px 18px" },
      { color: "rgba(70, 110, 255, 0.3)", pos: "100% 27%", size: "5px 10px" },
      { color: "rgba(110, 90, 230, 0.3)", pos: "100% 27%", size: "11px 12px" }
    ]
  },
  sunset: {
    border: [
      { color: "rgb(255, 180, 50)", pos: "2% 68%", size: "9px 18px" },
      { color: "rgb(255, 150, 40)", pos: "2% 68%", size: "4px 8px" },
      { color: "rgb(255, 80, 60)", pos: "72% -3%", size: "59px 9px" },
      { color: "rgb(255, 100, 80)", pos: "74% 100%", size: "42px 7px" },
      { color: "rgb(255, 60, 80)", pos: "100% 27%", size: "10px 17px" },
      { color: "rgb(255, 120, 60)", pos: "100% 27%", size: "10px 18px" },
      { color: "rgb(255, 200, 50)", pos: "100% 27%", size: "5px 10px" },
      { color: "rgb(255, 90, 70)", pos: "100% 27%", size: "11px 12px" }
    ],
    inner: [
      { color: "rgba(255, 180, 50, 0.5)", pos: "2% 68%", size: "9px 18px" },
      { color: "rgba(255, 150, 40, 0.45)", pos: "2% 68%", size: "4px 8px" },
      { color: "rgba(255, 80, 60, 0.35)", pos: "72% -3%", size: "59px 9px" },
      { color: "rgba(255, 100, 80, 0.35)", pos: "74% 100%", size: "42px 7px" },
      { color: "rgba(255, 60, 80, 0.3)", pos: "100% 27%", size: "10px 17px" },
      { color: "rgba(255, 120, 60, 0.4)", pos: "100% 27%", size: "10px 18px" },
      { color: "rgba(255, 200, 50, 0.3)", pos: "100% 27%", size: "5px 10px" },
      { color: "rgba(255, 90, 70, 0.3)", pos: "100% 27%", size: "11px 12px" }
    ]
  }
};
function Pe(t) {
  return He[t].border.map((a) => `radial-gradient(ellipse ${a.size} at ${a.pos}, ${a.color}, transparent)`).join(`,
    `);
}
function Be(t) {
  return He[t].inner.map((a) => `radial-gradient(ellipse ${a.size} at ${a.pos}, ${a.color}, transparent)`).join(`,
    `);
}
function Ee(t) {
  return C[t].border.map((a) => `radial-gradient(ellipse ${a.size} at ${a.pos}, ${a.color}, transparent)`).join(`,
    `);
}
function Ae(t) {
  const e = C[t], a = t === "mono" ? 0.225 : 0.45;
  return e.border.map((r) => {
    const o = r.color.replace("rgb(", "rgba(").replace(")", `, ${a})`);
    return `radial-gradient(ellipse ${r.size.split(" ").map((i) => {
      const c = parseInt(i);
      return `${Math.round(c * 0.9)}px`;
    }).join(" ")} at ${r.pos}, ${o}, transparent)`;
  }).join(`,
    `);
}
function _e(t, e) {
  const a = C[t];
  return e ? a.spike : a.spikeLt;
}
const je = {
  colorful: {
    dark: [
      { color: "rgb(255, 50, 100)", sizeW: 36, sizeH: 36, offsetX: 0, offsetY: 2 },
      { color: "rgb(40, 180, 220)", sizeW: 30, sizeH: 32, offsetX: 39, offsetY: 0 },
      { color: "rgb(50, 200, 80)", sizeW: 33, sizeH: 28, offsetX: -36, offsetY: 2 },
      { color: "rgb(180, 40, 240)", sizeW: 29, sizeH: 34, offsetX: -54, offsetY: 0 },
      { color: "rgb(255, 160, 30)", sizeW: 27, sizeH: 30, offsetX: 51, offsetY: -1 },
      { color: "rgb(100, 70, 255)", sizeW: 36, sizeH: 24, offsetX: 21, offsetY: 1 },
      { color: "rgb(40, 140, 255)", sizeW: 30, sizeH: 22, offsetX: -21, offsetY: 0 },
      { color: "rgb(240, 50, 180)", sizeW: 25, sizeH: 28, offsetX: 66, offsetY: 1 },
      { color: "rgb(30, 185, 170)", sizeW: 23, sizeH: 30, offsetX: -66, offsetY: -1 }
    ],
    light: [
      { color: "rgb(255, 50, 100)", sizeW: 45, sizeH: 36, offsetX: 0, offsetY: 2 },
      { color: "rgb(40, 140, 255)", sizeW: 35, sizeH: 32, offsetX: 65, offsetY: 0 },
      { color: "rgb(50, 200, 80)", sizeW: 40, sizeH: 28, offsetX: -60, offsetY: 2 },
      { color: "rgb(180, 40, 240)", sizeW: 35, sizeH: 34, offsetX: -90, offsetY: 0 },
      { color: "rgb(30, 185, 170)", sizeW: 38, sizeH: 30, offsetX: 85, offsetY: -1 },
      { color: "rgb(100, 70, 255)", sizeW: 50, sizeH: 24, offsetX: 35, offsetY: 1 },
      { color: "rgb(40, 140, 255)", sizeW: 40, sizeH: 22, offsetX: -35, offsetY: 0 },
      { color: "rgb(255, 120, 40)", sizeW: 35, sizeH: 28, offsetX: 110, offsetY: 1 },
      { color: "rgb(240, 50, 180)", sizeW: 30, sizeH: 30, offsetX: -110, offsetY: -1 }
    ]
  },
  mono: {
    dark: [
      { color: "rgb(200, 200, 200)", sizeW: 36, sizeH: 36, offsetX: 0, offsetY: 2 },
      { color: "rgb(170, 170, 170)", sizeW: 30, sizeH: 32, offsetX: 39, offsetY: 0 },
      { color: "rgb(155, 155, 155)", sizeW: 33, sizeH: 28, offsetX: -36, offsetY: 2 },
      { color: "rgb(185, 185, 185)", sizeW: 29, sizeH: 34, offsetX: -54, offsetY: 0 },
      { color: "rgb(165, 165, 165)", sizeW: 27, sizeH: 30, offsetX: 51, offsetY: -1 },
      { color: "rgb(180, 180, 180)", sizeW: 36, sizeH: 24, offsetX: 21, offsetY: 1 },
      { color: "rgb(160, 160, 160)", sizeW: 30, sizeH: 22, offsetX: -21, offsetY: 0 },
      { color: "rgb(175, 175, 175)", sizeW: 25, sizeH: 28, offsetX: 66, offsetY: 1 },
      { color: "rgb(190, 190, 190)", sizeW: 23, sizeH: 30, offsetX: -66, offsetY: -1 }
    ],
    light: [
      { color: "rgb(100, 100, 100)", sizeW: 45, sizeH: 36, offsetX: 0, offsetY: 2 },
      { color: "rgb(80, 80, 80)", sizeW: 35, sizeH: 32, offsetX: 65, offsetY: 0 },
      { color: "rgb(90, 90, 90)", sizeW: 40, sizeH: 28, offsetX: -60, offsetY: 2 },
      { color: "rgb(70, 70, 70)", sizeW: 35, sizeH: 34, offsetX: -90, offsetY: 0 },
      { color: "rgb(85, 85, 85)", sizeW: 38, sizeH: 30, offsetX: 85, offsetY: -1 },
      { color: "rgb(95, 95, 95)", sizeW: 50, sizeH: 24, offsetX: 35, offsetY: 1 },
      { color: "rgb(75, 75, 75)", sizeW: 40, sizeH: 22, offsetX: -35, offsetY: 0 },
      { color: "rgb(105, 105, 105)", sizeW: 35, sizeH: 28, offsetX: 110, offsetY: 1 },
      { color: "rgb(65, 65, 65)", sizeW: 30, sizeH: 30, offsetX: -110, offsetY: -1 }
    ]
  },
  ocean: {
    dark: [
      { color: "rgb(100, 80, 220)", sizeW: 36, sizeH: 36, offsetX: 0, offsetY: 2 },
      { color: "rgb(60, 120, 255)", sizeW: 30, sizeH: 32, offsetX: 39, offsetY: 0 },
      { color: "rgb(80, 100, 200)", sizeW: 33, sizeH: 28, offsetX: -36, offsetY: 2 },
      { color: "rgb(130, 70, 255)", sizeW: 29, sizeH: 34, offsetX: -54, offsetY: 0 },
      { color: "rgb(70, 130, 255)", sizeW: 27, sizeH: 30, offsetX: 51, offsetY: -1 },
      { color: "rgb(120, 80, 255)", sizeW: 36, sizeH: 24, offsetX: 21, offsetY: 1 },
      { color: "rgb(90, 110, 230)", sizeW: 30, sizeH: 22, offsetX: -21, offsetY: 0 },
      { color: "rgb(110, 90, 240)", sizeW: 25, sizeH: 28, offsetX: 66, offsetY: 1 },
      { color: "rgb(140, 100, 255)", sizeW: 23, sizeH: 30, offsetX: -66, offsetY: -1 }
    ],
    light: [
      { color: "rgb(80, 60, 200)", sizeW: 45, sizeH: 36, offsetX: 0, offsetY: 2 },
      { color: "rgb(50, 100, 220)", sizeW: 35, sizeH: 32, offsetX: 65, offsetY: 0 },
      { color: "rgb(70, 90, 190)", sizeW: 40, sizeH: 28, offsetX: -60, offsetY: 2 },
      { color: "rgb(110, 60, 220)", sizeW: 35, sizeH: 34, offsetX: -90, offsetY: 0 },
      { color: "rgb(60, 110, 230)", sizeW: 38, sizeH: 30, offsetX: 85, offsetY: -1 },
      { color: "rgb(100, 70, 240)", sizeW: 50, sizeH: 24, offsetX: 35, offsetY: 1 },
      { color: "rgb(80, 100, 210)", sizeW: 40, sizeH: 22, offsetX: -35, offsetY: 0 },
      { color: "rgb(90, 80, 225)", sizeW: 35, sizeH: 28, offsetX: 110, offsetY: 1 },
      { color: "rgb(120, 90, 245)", sizeW: 30, sizeH: 30, offsetX: -110, offsetY: -1 }
    ]
  },
  sunset: {
    dark: [
      { color: "rgb(255, 100, 60)", sizeW: 36, sizeH: 36, offsetX: 0, offsetY: 2 },
      { color: "rgb(255, 180, 50)", sizeW: 30, sizeH: 32, offsetX: 39, offsetY: 0 },
      { color: "rgb(255, 140, 70)", sizeW: 33, sizeH: 28, offsetX: -36, offsetY: 2 },
      { color: "rgb(255, 80, 80)", sizeW: 29, sizeH: 34, offsetX: -54, offsetY: 0 },
      { color: "rgb(255, 200, 60)", sizeW: 27, sizeH: 30, offsetX: 51, offsetY: -1 },
      { color: "rgb(255, 120, 50)", sizeW: 36, sizeH: 24, offsetX: 21, offsetY: 1 },
      { color: "rgb(255, 160, 80)", sizeW: 30, sizeH: 22, offsetX: -21, offsetY: 0 },
      { color: "rgb(255, 90, 60)", sizeW: 25, sizeH: 28, offsetX: 66, offsetY: 1 },
      { color: "rgb(255, 70, 70)", sizeW: 23, sizeH: 30, offsetX: -66, offsetY: -1 }
    ],
    light: [
      { color: "rgb(220, 80, 40)", sizeW: 45, sizeH: 36, offsetX: 0, offsetY: 2 },
      { color: "rgb(230, 150, 30)", sizeW: 35, sizeH: 32, offsetX: 65, offsetY: 0 },
      { color: "rgb(210, 110, 50)", sizeW: 40, sizeH: 28, offsetX: -60, offsetY: 2 },
      { color: "rgb(200, 60, 60)", sizeW: 35, sizeH: 34, offsetX: -90, offsetY: 0 },
      { color: "rgb(220, 170, 40)", sizeW: 38, sizeH: 30, offsetX: 85, offsetY: -1 },
      { color: "rgb(210, 100, 30)", sizeW: 50, sizeH: 24, offsetX: 35, offsetY: 1 },
      { color: "rgb(230, 130, 60)", sizeW: 40, sizeH: 22, offsetX: -35, offsetY: 0 },
      { color: "rgb(190, 70, 50)", sizeW: 35, sizeH: 28, offsetX: 110, offsetY: 1 },
      { color: "rgb(180, 50, 50)", sizeW: 30, sizeH: 30, offsetX: -110, offsetY: -1 }
    ]
  }
};
function Te(t, e, a) {
  return je[t][e ? "dark" : "light"].map((o) => {
    const s = o.offsetX === 0 ? "" : o.offsetX > 0 ? ` + ${o.offsetX}px` : ` - ${Math.abs(o.offsetX)}px`, i = o.offsetY === 0 ? "" : o.offsetY > 0 ? ` + ${o.offsetY}px` : ` - ${Math.abs(o.offsetY)}px`;
    return `radial-gradient(ellipse calc(${o.sizeW}px * var(--beam-w-${a})) calc(${o.sizeH}px * var(--beam-h-${a})) at calc(var(--beam-x-${a}) * 100%${s}) calc(100%${i}), ${o.color}, transparent)`;
  }).join(`,
       `);
}
const Ne = {
  colorful: [
    { color: "rgba(255, 50, 100, 0.48)", sizeW: 33, sizeH: 30, offsetX: 0, offsetY: 0 },
    { color: "rgba(40, 180, 220, 0.42)", sizeW: 24, sizeH: 26, offsetX: 39, offsetY: -3 },
    { color: "rgba(50, 200, 80, 0.48)", sizeW: 27, sizeH: 24, offsetX: -36, offsetY: 0 },
    { color: "rgba(180, 40, 240, 0.42)", sizeW: 23, sizeH: 28, offsetX: -54, offsetY: -2 },
    { color: "rgba(255, 160, 30, 0.50)", sizeW: 24, sizeH: 24, offsetX: 51, offsetY: -1 },
    { color: "rgba(100, 70, 255, 0.45)", sizeW: 30, sizeH: 20, offsetX: 21, offsetY: 0 },
    { color: "rgba(40, 140, 255, 0.40)", sizeW: 25, sizeH: 18, offsetX: -21, offsetY: -2 },
    { color: "rgba(240, 50, 180, 0.45)", sizeW: 21, sizeH: 24, offsetX: 66, offsetY: 0 },
    { color: "rgba(30, 185, 170, 0.52)", sizeW: 18, sizeH: 26, offsetX: -66, offsetY: -1 }
  ],
  mono: [
    { color: "rgba(200, 200, 200, 0.48)", sizeW: 33, sizeH: 30, offsetX: 0, offsetY: 0 },
    { color: "rgba(170, 170, 170, 0.42)", sizeW: 24, sizeH: 26, offsetX: 39, offsetY: -3 },
    { color: "rgba(155, 155, 155, 0.48)", sizeW: 27, sizeH: 24, offsetX: -36, offsetY: 0 },
    { color: "rgba(185, 185, 185, 0.42)", sizeW: 23, sizeH: 28, offsetX: -54, offsetY: -2 },
    { color: "rgba(165, 165, 165, 0.50)", sizeW: 24, sizeH: 24, offsetX: 51, offsetY: -1 },
    { color: "rgba(180, 180, 180, 0.45)", sizeW: 30, sizeH: 20, offsetX: 21, offsetY: 0 },
    { color: "rgba(160, 160, 160, 0.40)", sizeW: 25, sizeH: 18, offsetX: -21, offsetY: -2 },
    { color: "rgba(175, 175, 175, 0.45)", sizeW: 21, sizeH: 24, offsetX: 66, offsetY: 0 },
    { color: "rgba(190, 190, 190, 0.52)", sizeW: 18, sizeH: 26, offsetX: -66, offsetY: -1 }
  ],
  ocean: [
    { color: "rgba(100, 80, 220, 0.48)", sizeW: 33, sizeH: 30, offsetX: 0, offsetY: 0 },
    { color: "rgba(60, 120, 255, 0.42)", sizeW: 24, sizeH: 26, offsetX: 39, offsetY: -3 },
    { color: "rgba(80, 100, 200, 0.48)", sizeW: 27, sizeH: 24, offsetX: -36, offsetY: 0 },
    { color: "rgba(130, 70, 255, 0.42)", sizeW: 23, sizeH: 28, offsetX: -54, offsetY: -2 },
    { color: "rgba(70, 130, 255, 0.50)", sizeW: 24, sizeH: 24, offsetX: 51, offsetY: -1 },
    { color: "rgba(120, 80, 255, 0.45)", sizeW: 30, sizeH: 20, offsetX: 21, offsetY: 0 },
    { color: "rgba(90, 110, 230, 0.40)", sizeW: 25, sizeH: 18, offsetX: -21, offsetY: -2 },
    { color: "rgba(110, 90, 240, 0.45)", sizeW: 21, sizeH: 24, offsetX: 66, offsetY: 0 },
    { color: "rgba(140, 100, 255, 0.52)", sizeW: 18, sizeH: 26, offsetX: -66, offsetY: -1 }
  ],
  sunset: [
    { color: "rgba(255, 100, 60, 0.48)", sizeW: 33, sizeH: 30, offsetX: 0, offsetY: 0 },
    { color: "rgba(255, 180, 50, 0.42)", sizeW: 24, sizeH: 26, offsetX: 39, offsetY: -3 },
    { color: "rgba(255, 140, 70, 0.48)", sizeW: 27, sizeH: 24, offsetX: -36, offsetY: 0 },
    { color: "rgba(255, 80, 80, 0.42)", sizeW: 23, sizeH: 28, offsetX: -54, offsetY: -2 },
    { color: "rgba(255, 200, 60, 0.50)", sizeW: 24, sizeH: 24, offsetX: 51, offsetY: -1 },
    { color: "rgba(255, 120, 50, 0.45)", sizeW: 30, sizeH: 20, offsetX: 21, offsetY: 0 },
    { color: "rgba(255, 160, 80, 0.40)", sizeW: 25, sizeH: 18, offsetX: -21, offsetY: -2 },
    { color: "rgba(255, 90, 60, 0.45)", sizeW: 21, sizeH: 24, offsetX: 66, offsetY: 0 },
    { color: "rgba(255, 70, 70, 0.52)", sizeW: 18, sizeH: 26, offsetX: -66, offsetY: -1 }
  ]
};
function Ve(t, e) {
  return Ne[t].map((r) => {
    const o = r.offsetX === 0 ? "" : r.offsetX > 0 ? ` + ${r.offsetX}px` : ` - ${Math.abs(r.offsetX)}px`, s = r.offsetY === 0 ? "" : ` - ${Math.abs(r.offsetY)}px`;
    return `radial-gradient(ellipse calc(${r.sizeW}px * var(--beam-w-${e})) calc(${r.sizeH}px * var(--beam-h-${e})) at calc(var(--beam-x-${e}) * 100%${o}) calc(100%${s}), ${r.color}, transparent)`;
  }).join(`,
    `);
}
const De = {
  colorful: {
    dark: {
      spikes: [
        { color1: "rgb(100, 70, 255)", color2: "rgba(100, 70, 255, 1)" },
        // 36%
        { color1: "rgba(255, 170, 40, 0.59)", color2: "rgba(255, 170, 40, 0.29)" },
        // 50%
        { color1: "rgb(50, 200, 100)", color2: "rgba(50, 200, 100, 1)" },
        // 64%
        { color1: "rgba(200, 50, 240, 0.91)", color2: "rgba(200, 50, 240, 0.45)" },
        // 78%
        { color1: "rgb(40, 140, 255)", color2: "rgba(40, 140, 255, 1)" }
        // 92%
      ]
    },
    light: {
      spikes: [
        { color1: "rgb(80, 50, 200)", color2: "rgba(80, 50, 200, 0.8)" },
        // 36%
        { color1: "rgba(210, 130, 0, 0.7)", color2: "rgba(210, 130, 0, 0.46)" },
        // 50%
        { color1: "rgb(30, 160, 70)", color2: "rgba(30, 160, 70, 0.82)" },
        // 64%
        { color1: "rgb(160, 30, 190)", color2: "rgba(160, 30, 190, 0.7)" },
        // 78%
        { color1: "rgb(30, 100, 200)", color2: "rgba(30, 100, 200, 0.78)" }
        // 92%
      ]
    }
  },
  mono: {
    dark: {
      spikes: [
        { color1: "rgb(200, 200, 200)", color2: "rgba(200, 200, 200, 1)" },
        { color1: "rgba(180, 180, 180, 0.59)", color2: "rgba(180, 180, 180, 0.29)" },
        { color1: "rgb(190, 190, 190)", color2: "rgba(190, 190, 190, 1)" },
        { color1: "rgba(170, 170, 170, 0.91)", color2: "rgba(170, 170, 170, 0.45)" },
        { color1: "rgb(185, 185, 185)", color2: "rgba(185, 185, 185, 1)" }
      ]
    },
    light: {
      spikes: [
        { color1: "rgb(80, 80, 80)", color2: "rgba(80, 80, 80, 0.8)" },
        { color1: "rgba(100, 100, 100, 0.7)", color2: "rgba(100, 100, 100, 0.46)" },
        { color1: "rgb(70, 70, 70)", color2: "rgba(70, 70, 70, 0.82)" },
        { color1: "rgb(90, 90, 90)", color2: "rgba(90, 90, 90, 0.7)" },
        { color1: "rgb(85, 85, 85)", color2: "rgba(85, 85, 85, 0.78)" }
      ]
    }
  },
  ocean: {
    dark: {
      spikes: [
        { color1: "rgb(100, 80, 255)", color2: "rgb(100, 80, 255)" },
        { color1: "rgba(80, 130, 220, 0.59)", color2: "rgba(80, 130, 220, 0.29)" },
        { color1: "rgb(60, 100, 255)", color2: "rgb(60, 100, 255)" },
        { color1: "rgba(90, 120, 200, 0.91)", color2: "rgba(90, 120, 200, 0.45)" },
        { color1: "rgb(120, 90, 255)", color2: "rgb(120, 90, 255)" }
      ]
    },
    light: {
      spikes: [
        { color1: "rgb(50, 40, 180)", color2: "rgba(50, 40, 180, 0.8)" },
        { color1: "rgba(40, 80, 200, 0.7)", color2: "rgba(40, 80, 200, 0.46)" },
        { color1: "rgb(30, 50, 190)", color2: "rgba(30, 50, 190, 0.82)" },
        { color1: "rgb(60, 90, 180)", color2: "rgba(60, 90, 180, 0.7)" },
        { color1: "rgb(70, 60, 200)", color2: "rgba(70, 60, 200, 0.78)" }
      ]
    }
  },
  sunset: {
    dark: {
      spikes: [
        { color1: "rgb(255, 100, 80)", color2: "rgb(255, 100, 80)" },
        { color1: "rgba(255, 150, 80, 0.59)", color2: "rgba(255, 150, 80, 0.29)" },
        { color1: "rgb(255, 80, 60)", color2: "rgb(255, 80, 60)" },
        { color1: "rgba(255, 120, 50, 0.91)", color2: "rgba(255, 120, 50, 0.45)" },
        { color1: "rgb(255, 140, 70)", color2: "rgb(255, 140, 70)" }
      ]
    },
    light: {
      spikes: [
        { color1: "rgb(200, 60, 30)", color2: "rgba(200, 60, 30, 0.8)" },
        { color1: "rgba(220, 100, 20, 0.7)", color2: "rgba(220, 100, 20, 0.46)" },
        { color1: "rgb(180, 40, 20)", color2: "rgba(180, 40, 20, 0.82)" },
        { color1: "rgb(210, 80, 10)", color2: "rgba(210, 80, 10, 0.7)" },
        { color1: "rgb(190, 70, 30)", color2: "rgba(190, 70, 30, 0.78)" }
      ]
    }
  }
};
function K(t, e) {
  const a = t.match(/^rgba\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*[\d.]+\s*\)$/);
  if (a) return `rgba(${a[1]}, ${a[2]}, ${a[3]}, ${e})`;
  const r = t.match(/^rgb\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)$/);
  return r ? `rgba(${r[1]}, ${r[2]}, ${r[3]}, ${e})` : t;
}
function q(t, e) {
  const a = t.match(/^rgba\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)$/);
  if (a) return `rgba(${a[1]}, ${a[2]}, ${a[3]}, ${(parseFloat(a[4]) * e).toFixed(2)})`;
  const r = t.match(/^rgb\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*\)$/);
  return r ? `rgba(${r[1]}, ${r[2]}, ${r[3]}, ${e.toFixed(2)})` : t;
}
function Ue(t, e, a) {
  const r = _e(t, e), o = De[t][e ? "dark" : "light"], s = t === "mono", i = s ? 0.14 : 1, c = s ? q(r.primary, 0.14) : r.primary, p = s ? q(r.primary, 0.09) : r.primary, b = s ? q(r.secondary, 0.12) : r.secondary, m = s ? K(r.secondary, 0.06) : K(r.secondary, 0.49), n = o.spikes.map(
    (v) => s ? { color1: q(v.color1, i), color2: q(v.color2, i * 0.7) } : v
  ), l = s ? "12px" : "0.8px", d = s ? "14px" : "2px", k = s ? "12px" : "1.2px", f = s ? "10px" : "0.6px", g = s ? "42px" : "92px", W = s ? "38px" : "72px", Y = s ? "40px" : "85px", z = s ? "32px" : "60px", H = s ? "12px" : "1px", $ = s ? "rgba(255, 255, 255, 0.5)" : "rgba(255, 255, 255, 1)", w = s ? "rgba(255, 255, 255, 0.45)" : "rgba(255, 255, 255, 0.9)", y = s ? "rgba(255, 255, 255, 0.25)" : "rgba(255, 255, 255, 0.5)", x = s ? "rgba(255, 255, 255, 0.15)" : "rgba(255, 255, 255, 0.3)", X = s ? "rgba(255, 255, 255, 0.06)" : "rgba(255, 255, 255, 0.12)", u = s ? "rgba(255, 255, 255, 0.015)" : "rgba(255, 255, 255, 0.03)";
  if (e)
    return `radial-gradient(ellipse calc(${l} * var(--beam-spike-${a})) calc(${g} * var(--beam-h-${a})) at 8% calc(100% - 2px), ${c}, ${p} 30%, transparent 88%),
       radial-gradient(ellipse calc(10px * var(--beam-spike2-${a})) calc(35px * var(--beam-h-${a})) at 22% calc(100% - 4px), ${b}, ${m} 50%, transparent 95%),
       radial-gradient(ellipse calc(${d} * (2 - var(--beam-spike-${a}))) calc(${W} * var(--beam-h-${a})) at 36% calc(100% - 3px), ${n[0].color1}, ${n[0].color2} 40%, transparent 90%),
       radial-gradient(ellipse calc(14px * var(--beam-spike2-${a})) calc(28px * var(--beam-h-${a})) at 50% calc(100% - 2px), ${n[1].color1}, ${n[1].color2} 55%, transparent 96%),
       radial-gradient(ellipse calc(${k} * (2 - var(--beam-spike2-${a}))) calc(${Y} * var(--beam-h-${a})) at 64% calc(100% - 4px), ${n[2].color1}, ${n[2].color2} 35%, transparent 89%),
       radial-gradient(ellipse calc(7px * var(--beam-spike-${a})) calc(45px * var(--beam-h-${a})) at 78% calc(100% - 2px), ${n[3].color1}, ${n[3].color2} 48%, transparent 94%),
       radial-gradient(ellipse calc(${f} * (2 - var(--beam-spike-${a}))) calc(${z} * var(--beam-h-${a})) at 92% calc(100% - 3px), ${n[4].color1}, ${n[4].color2} 42%, transparent 91%),
       radial-gradient(ellipse calc(21px * var(--beam-spike-${a})) calc(15px * var(--beam-spike2-${a})) at calc(var(--beam-x-${a}) * 100%) calc(100% + 1px), ${$} 0%, ${w} 20%, ${y} 50%, transparent 100%),
       radial-gradient(ellipse calc(42px * var(--beam-w-${a})) calc(40px * var(--beam-h-${a})) at calc(var(--beam-x-${a}) * 100%) 100%, ${x} 0%, ${X} 25%, ${u} 55%, transparent 80%)`;
  {
    const v = s ? q(r.primary, 0.11) : K(r.primary, 0.85), S = s ? q(r.secondary, 0.09) : K(r.secondary, 0.7);
    return `radial-gradient(ellipse calc(${l} * var(--beam-spike-${a})) calc(${g} * var(--beam-h-${a})) at 8% calc(100% - 2px), ${c}, ${v} 30%, transparent 88%),
       radial-gradient(ellipse calc(10px * var(--beam-spike2-${a})) calc(35px * var(--beam-h-${a})) at 22% calc(100% - 4px), ${b}, ${S} 50%, transparent 95%),
       radial-gradient(ellipse calc(${d} * (2 - var(--beam-spike-${a}))) calc(${W} * var(--beam-h-${a})) at 36% calc(100% - 3px), ${n[0].color1}, ${n[0].color2} 40%, transparent 90%),
       radial-gradient(ellipse calc(14px * var(--beam-spike2-${a})) calc(28px * var(--beam-h-${a})) at 50% calc(100% - 2px), ${n[1].color1}, ${n[1].color2} 55%, transparent 96%),
       radial-gradient(ellipse calc(${k} * (2 - var(--beam-spike2-${a}))) calc(${Y} * var(--beam-h-${a})) at 64% calc(100% - 4px), ${n[2].color1}, ${n[2].color2} 35%, transparent 89%),
       radial-gradient(ellipse calc(7px * var(--beam-spike-${a})) calc(45px * var(--beam-h-${a})) at 78% calc(100% - 2px), ${n[3].color1}, ${n[3].color2} 48%, transparent 94%),
       radial-gradient(ellipse calc(${H} * (2 - var(--beam-spike-${a}))) calc(${z} * var(--beam-h-${a})) at 92% calc(100% - 3px), ${n[4].color1}, ${n[4].color2} 42%, transparent 91%),
       radial-gradient(ellipse calc(50px * var(--beam-w-${a})) calc(32px * var(--beam-h-${a})) at calc(var(--beam-x-${a}) * 100%) calc(100%), rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0.18) 30%, rgba(0, 0, 0, 0.03) 60%, transparent 85%)`;
  }
}
const Xe = [
  { region: 1, quad: "tl" },
  { region: 2, quad: "tl" },
  { region: 3, quad: "bl" },
  { region: 1, quad: "bl" },
  { region: 2, quad: "br" },
  { region: 3, quad: "br" },
  { region: 1, quad: "tr" },
  { region: 2, quad: "tr" },
  { region: 3, quad: "tr" }
], Ke = [
  [65, 35],
  [55, 30],
  [35, 65],
  [15, 30],
  [173, 28],
  [80, 22],
  [69, 28],
  [22, 38],
  [47, 44]
], Qe = [
  { ci: 0, region: 1, quad: "tl", w: 84, h: 48 },
  { ci: 1, region: 2, quad: "tl", w: 72, h: 42 },
  { ci: 2, region: 3, quad: "bl", w: 48, h: 84 },
  { ci: 4, region: 2, quad: "br", w: 216, h: 38 },
  { ci: 5, region: 3, quad: "br", w: 102, h: 31 },
  { ci: 6, region: 1, quad: "tr", w: 89, h: 38 },
  { ci: 8, region: 3, quad: "tr", w: 62, h: 58 }
], ke = [
  { ci: 0, region: 1, quad: "tl", w: 80, h: 19, x: "27%", y: "0%" },
  { ci: 6, region: 2, quad: "tr", w: 74, h: 11, x: "73%", y: "-1%" },
  { ci: 7, region: 3, quad: "tr", w: 15, h: 44, x: "100%", y: "33%" },
  { ci: 8, region: 1, quad: "br", w: 19, h: 38, x: "101%", y: "72%" },
  { ci: 4, region: 2, quad: "br", w: 84, h: 13, x: "67%", y: "100%" },
  { ci: 1, region: 3, quad: "bl", w: 60, h: 21, x: "24%", y: "101%" },
  { ci: 2, region: 1, quad: "bl", w: 17, h: 40, x: "0%", y: "60%" },
  { ci: 3, region: 2, quad: "tl", w: 13, h: 32, x: "-1%", y: "28%" }
], Ze = [
  { ci: 0, region: 1, quad: "tl", w: 110, h: 30, x: "27%", y: "3%" },
  { ci: 6, region: 2, quad: "tr", w: 100, h: 20, x: "73%", y: "1%" },
  { ci: 7, region: 3, quad: "tr", w: 26, h: 62, x: "100%", y: "33%" },
  { ci: 8, region: 1, quad: "br", w: 30, h: 56, x: "101%", y: "72%" },
  { ci: 4, region: 2, quad: "br", w: 120, h: 22, x: "67%", y: "99%" },
  { ci: 1, region: 3, quad: "bl", w: 88, h: 32, x: "24%", y: "99%" },
  { ci: 2, region: 1, quad: "bl", w: 28, h: 58, x: "0%", y: "60%" }
];
function Je(t, e, a) {
  const r = t.match(/^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/);
  return `rgba(${r ? `${r[1]}, ${r[2]}, ${r[3]}` : "255, 255, 255"}, var(--bop-${e}-${a}))`;
}
function be(t, e, a, r, o, s, i, c) {
  return `radial-gradient(ellipse calc(${e}px * var(--bw${r}-${c}) * var(--pulse-glow-sx, 1) * var(--pulse-glow-boost, 1)) calc(${a}px * var(--bh${r}-${c}) * var(--bgh-${c}) * var(--pulse-glow-sy, 1) * var(--pulse-glow-boost, 1)) at calc(${s} + var(--bx${r}-${c})) calc(${i} + var(--by${r}-${c})), ${Je(t, o, c)}, transparent)`;
}
function ea(t, e) {
  return C[t].border.map((a, r) => {
    const { region: o, quad: s } = Xe[r], [i, c] = a.pos.split(" "), [p, b] = a.size.split(" ").map(parseFloat);
    return be(a.color, p, b, o, s, i, c, e);
  }).join(`,
    `);
}
function aa(t, e, a) {
  const o = C[t].border.map((b, m) => {
    const { region: n, quad: l } = Xe[m], [d, k] = b.pos.split(" "), [f, g] = Ke[m];
    return be(b.color, f, g, n, l, d, k, e);
  }), s = a ? "255, 255, 255" : "0, 0, 0", i = a ? 0.18 : 0.08, p = [
    ["0%", "0%", "tl"],
    ["100%", "0%", "tr"],
    ["0%", "100%", "bl"],
    ["100%", "100%", "br"]
  ].map(
    ([b, m, n]) => `radial-gradient(ellipse 60px 60px at ${b} ${m}, rgba(${s}, calc(${i} * var(--bop-${n}-${e}))), transparent 70%)`
  );
  return [...o, ...p].join(`,
    `);
}
function we(t, e, a) {
  const r = C[e].border;
  return t.map((o) => {
    const s = r[o.ci], [i, c] = s.pos.split(" ");
    return be(s.color, o.w, o.h, o.region, o.quad, o.x ?? i, o.y ?? c, a);
  }).join(`,
    `);
}
function Ye(t, e, a) {
  const r = C[e].border, o = +a.toFixed(3);
  return t.map((s) => {
    const i = r[s.ci], [c, p] = i.pos.split(" "), b = s.x ?? c, m = s.y ?? p, n = i.color.match(/^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/), l = n ? `${n[1]}, ${n[2]}, ${n[3]}` : "255, 255, 255";
    return `radial-gradient(ellipse calc(${s.w}px * var(--pulse-glow-sx, 1) * var(--pulse-glow-boost, 1)) calc(${s.h}px * var(--pulse-glow-sy, 1) * var(--pulse-glow-boost, 1)) at ${b} ${m}, rgba(${l}, ${o}), transparent)`;
  }).join(`,
    `);
}
function _(t) {
  return `
[data-beam="${t}"][data-paused],
[data-beam="${t}"][data-paused]::after,
[data-beam="${t}"][data-paused]::before,
[data-beam="${t}"][data-paused] [data-beam-bloom] {
  animation-play-state: paused !important;
}`;
}
function Oe(t) {
  const e = ["bw1", "bh1", "bw2", "bh2", "bw3", "bh3", "bgh", "bop-tl", "bop-tr", "bop-bl", "bop-br"], a = ["bx1", "by1", "bx2", "by2", "bx3", "by3"], r = e.map(
    (s) => `@property --${s}-${t} {
  syntax: "<number>";
  initial-value: 1;
  inherits: true;
}`
  ).join(`

`), o = a.map(
    (s) => `@property --${s}-${t} {
  syntax: "<length>";
  initial-value: 0px;
  inherits: true;
}`
  ).join(`

`);
  return `${r}

${o}

@property --beam-opacity-${t} {
  syntax: "<number>";
  initial-value: 0;
  inherits: true;
}

@property --beam-hue-${t} {
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: true;
}`;
}
function pe(t, e, a) {
  const r = e === "dark", o = a / 2.3;
  return t === "pulse-inner" ? {
    sp: 0.28,
    dr: r ? 33 : 40,
    op: r ? 0.48 : 0.45,
    gh: r ? 0.34 : 0.22,
    bs: (r ? 1.9 : 2.6) * o,
    ss: (r ? 2.6 : 4.6) * o,
    ghs: (r ? 2.4 : 5.5) * o,
    // Full hue revolution period (seconds) — colors continuously cycle.
    huePeriod: 16
  } : {
    sp: r ? 0.28 : 0.36,
    dr: r ? 14 : 19,
    op: r ? 0.46 : 0,
    gh: r ? 0.16 : 0.58,
    bs: (r ? 2.3 : 3.7) * o,
    ss: (r ? 6.4 : 4.6) * o,
    ghs: (r ? 2.4 : 3.8) * o,
    // Full hue revolution period (seconds) — colors continuously cycle.
    huePeriod: 14
  };
}
function ra(t, e) {
  const { sp: a, dr: r, op: o, gh: s, bs: i, ss: c, ghs: p } = e;
  return [
    { prop: `--bw1-${t}`, a: 1 - a, b: 1 + a * 1.1, period: c * 0.9, delay: 0, unit: "" },
    { prop: `--bh1-${t}`, a: 1 + a * 0.9, b: 1 - a * 0.85, period: c * 1.26, delay: 0, unit: "" },
    { prop: `--bx1-${t}`, a: -r, b: r * 0.9, period: i * 1.6, delay: 0, unit: "px" },
    { prop: `--by1-${t}`, a: r * 0.55, b: -r * 0.7, period: i * 1.6, delay: 0, unit: "px" },
    { prop: `--bw2-${t}`, a: 1 + a, b: 1 - a * 0.85, period: c * 1.1, delay: 0, unit: "" },
    { prop: `--bh2-${t}`, a: 1 - a * 0.8, b: 1 + a * 1.05, period: c * 0.81, delay: 0, unit: "" },
    { prop: `--bx2-${t}`, a: r * 0.8, b: -r * 0.9, period: i * 1.88, delay: 0, unit: "px" },
    { prop: `--by2-${t}`, a: -r, b: r * 0.65, period: i * 1.88, delay: 0, unit: "px" },
    { prop: `--bw3-${t}`, a: 1 - a * 0.6, b: 1 + a * 1.15, period: c * 0.98, delay: 0, unit: "" },
    { prop: `--bh3-${t}`, a: 1 + a * 0.75, b: 1 - a, period: c * 1.4, delay: 0, unit: "" },
    { prop: `--bx3-${t}`, a: -r * 0.6, b: r, period: i * 1.45, delay: 0, unit: "px" },
    { prop: `--by3-${t}`, a: -r * 0.85, b: r * 0.45, period: i * 1.45, delay: 0, unit: "px" },
    { prop: `--bgh-${t}`, a: 1 - s, b: 1 + s, period: p, delay: 0, unit: "" },
    { prop: `--bop-tl-${t}`, a: 1 - o, b: 1, period: i, delay: 0, unit: "" },
    { prop: `--bop-tr-${t}`, a: 1 - o, b: 1, period: i * 1.32, delay: i * 0.28, unit: "" },
    { prop: `--bop-bl-${t}`, a: 1 - o, b: 1, period: i * 0.84, delay: i * 0.55, unit: "" },
    { prop: `--bop-br-${t}`, a: 1 - o, b: 1, period: i * 1.58, delay: i * 0.83, unit: "" }
  ];
}
function ta(t, e, a, r, o, s) {
  if (t !== "pulse-inner" && t !== "pulse-outside") return null;
  const i = pe(t, e, a);
  return {
    oscillators: ra(s, i),
    // Pulse colors continuously rotate a full hue circle so the palette is never
    // pinned to fixed edges (no more "always red top-right / green left").
    hue: o ? null : { prop: `--beam-hue-${s}`, range: 360, period: i.huePeriod, continuous: !0 }
  };
}
function Q(t, e, a) {
  return `  animation: ${e}-${t} ${a}s ease forwards;`;
}
function oa(t) {
  const { size: e } = t;
  return e === "line" ? ba(t) : e === "sm" ? sa(t) : e === "pulse-inner" ? na(t) : e === "pulse-outside" ? ca(t) : ia(t);
}
function sa(t) {
  const {
    id: e,
    borderRadius: a,
    borderWidth: r,
    duration: o,
    strokeOpacity: s,
    innerOpacity: i,
    bloomOpacity: c,
    innerShadow: p,
    colorVariant: b,
    staticColors: m,
    brightness: n,
    saturation: l,
    hueRange: d,
    theme: k
  } = t, f = Math.max(0, a - r), g = b === "mono" ? 0.5 : 1, W = s * g, Y = i * g, z = c * g, H = m ? "" : `animation: beam-hue-shift-${e} 12s ease-in-out infinite;`, $ = m ? "" : `
@keyframes beam-hue-shift-${e} {
  0% { filter: hue-rotate(calc(var(--beam-hue-base, 0deg) - ${d}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
  50% { filter: hue-rotate(calc(var(--beam-hue-base, 0deg) + ${d}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
  100% { filter: hue-rotate(calc(var(--beam-hue-base, 0deg) - ${d}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
}`, w = k === "dark", y = w ? `conic-gradient(
        from var(--beam-angle-${e}),
        transparent 0%, transparent 54%,
        rgba(255, 255, 255, 0.1) 57%,
        rgba(255, 255, 255, 0.3) 60%,
        rgba(255, 255, 255, 0.6) 63%,
        rgba(255, 255, 255, 0.75) 66%,
        rgba(255, 255, 255, 0.6) 69%,
        rgba(255, 255, 255, 0.3) 72%,
        rgba(255, 255, 255, 0.1) 75%,
        transparent 78%, transparent 100%
      )` : `conic-gradient(
        from var(--beam-angle-${e}),
        transparent 0%, transparent 54%,
        rgba(0, 0, 0, 0.08) 57%,
        rgba(0, 0, 0, 0.2) 60%,
        rgba(0, 0, 0, 0.4) 63%,
        rgba(0, 0, 0, 0.55) 66%,
        rgba(0, 0, 0, 0.4) 69%,
        rgba(0, 0, 0, 0.2) 72%,
        rgba(0, 0, 0, 0.08) 75%,
        transparent 78%, transparent 100%
      )`, x = Pe(b), X = Be(b), u = w ? `conic-gradient(
        from var(--beam-angle-${e}),
        transparent 0%, transparent 58%,
        rgba(255, 255, 255, 0.03) 62%,
        rgba(255, 255, 255, 0.08) 65%,
        rgba(255, 255, 255, 0.2) 67%,
        rgba(255, 255, 255, 0.45) 69%,
        rgba(255, 255, 255, 0.85) 70%,
        rgba(255, 255, 255, 0.85) 70.5%,
        rgba(255, 255, 255, 0.45) 71.5%,
        rgba(255, 255, 255, 0.2) 73%,
        rgba(255, 255, 255, 0.08) 75%,
        rgba(255, 255, 255, 0.03) 78%,
        transparent 82%
      )` : `conic-gradient(
        from var(--beam-angle-${e}),
        transparent 0%, transparent 58%,
        rgba(0, 0, 0, 0.02) 62%,
        rgba(0, 0, 0, 0.08) 65%,
        rgba(0, 0, 0, 0.2) 67%,
        rgba(0, 0, 0, 0.4) 69%,
        rgba(0, 0, 0, 0.6) 70%,
        rgba(0, 0, 0, 0.6) 70.5%,
        rgba(0, 0, 0, 0.4) 71.5%,
        rgba(0, 0, 0, 0.2) 73%,
        rgba(0, 0, 0, 0.08) 75%,
        rgba(0, 0, 0, 0.02) 78%,
        transparent 82%
      )`, v = `conic-gradient(
    from var(--beam-angle-${e}),
    transparent 0%, transparent 22%,
    rgba(255, 255, 255, 0.12) 28%, rgba(255, 255, 255, 0.4) 36%,
    white 46%, white 82%,
    rgba(255, 255, 255, 0.4) 88%, rgba(255, 255, 255, 0.12) 94%,
    transparent 97%, transparent 100%
  )`;
  return `
@property --beam-angle-${e} {
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: true;
}

@property --beam-opacity-${e} {
  syntax: "<number>";
  initial-value: 0;
  inherits: true;
}

[data-beam="${e}"] {
  position: relative;
  border-radius: ${a}px;
  overflow: hidden;
}

[data-beam="${e}"][data-active] {
  animation:
    beam-spin-${e} ${o}s linear infinite,
    beam-fade-in-${e} 0.6s ease forwards;
}

[data-beam="${e}"][data-fading] {
  animation:
    beam-spin-${e} ${o}s linear infinite,
    beam-fade-out-${e} 0.5s ease forwards;
}

[data-beam="${e}"][data-active]::after,
[data-beam="${e}"][data-fading]::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${f}px;
  padding: ${r}px;
  clip-path: inset(0 round ${a}px);
  background: ${y},${x};
  -webkit-mask:
    conic-gradient(
      from var(--beam-angle-${e}),
      transparent 0%, transparent 30%,
      rgba(255, 255, 255, 0.1) 36%, rgba(255, 255, 255, 0.35) 44%,
      white 52%, white 80%,
      rgba(255, 255, 255, 0.35) 86%, rgba(255, 255, 255, 0.1) 92%,
      transparent 95%, transparent 100%
    ),
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: source-in, xor;
  mask:
    conic-gradient(
      from var(--beam-angle-${e}),
      transparent 0%, transparent 30%,
      rgba(255, 255, 255, 0.1) 36%, rgba(255, 255, 255, 0.35) 44%,
      white 52%, white 80%,
      rgba(255, 255, 255, 0.35) 86%, rgba(255, 255, 255, 0.1) 92%,
      transparent 95%, transparent 100%
    ),
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: intersect, exclude;
  pointer-events: none;
  z-index: 2;
  opacity: calc(var(--beam-opacity-${e}) * ${W.toFixed(2)} * var(--beam-stroke-opacity, 1) * var(--beam-strength, 1));
  ${H}
}

[data-beam="${e}"][data-active]::before,
[data-beam="${e}"][data-fading]::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${a}px;
  clip-path: inset(0 round ${a}px);
  background: ${X};
  box-shadow: inset 0 0 5px 1px ${p};
  -webkit-mask-image: ${v};
  -webkit-mask-composite: source-over;
  mask-image: ${v};
  mask-composite: add;
  pointer-events: none;
  z-index: 1;
  opacity: calc(var(--beam-opacity-${e}) * ${Y.toFixed(2)} * var(--beam-inner-opacity, 1) * var(--beam-strength, 1));
  ${H}
}

[data-beam="${e}"] [data-beam-bloom] {
  display: none;
  position: absolute;
  inset: 0;
  border-radius: ${f}px;
  clip-path: inset(0 round ${a}px);
  background: ${u};
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  padding: ${r}px;
  filter: blur(8px) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)});
  pointer-events: none;
  z-index: 3;
  opacity: 0;
}

[data-beam="${e}"][data-active] [data-beam-bloom],
[data-beam="${e}"][data-fading] [data-beam-bloom] {
  display: block;
  opacity: calc(var(--beam-opacity-${e}) * ${z.toFixed(2)} * var(--beam-bloom-opacity, 1) * var(--beam-strength, 1));
}

@keyframes beam-spin-${e} {
  to { --beam-angle-${e}: 360deg; }
}

@keyframes beam-fade-in-${e} {
  to { --beam-opacity-${e}: 1; }
}

@keyframes beam-fade-out-${e} {
  from { --beam-opacity-${e}: 1; }
  to { --beam-opacity-${e}: 0; }
}
${$}
${_(e)}
`;
}
function ia(t) {
  const {
    id: e,
    borderRadius: a,
    borderWidth: r,
    duration: o,
    strokeOpacity: s,
    innerOpacity: i,
    bloomOpacity: c,
    innerShadow: p,
    colorVariant: b,
    staticColors: m,
    brightness: n,
    saturation: l,
    hueRange: d,
    theme: k
  } = t, f = Math.max(0, a - r), g = b === "mono" ? 0.5 : 1, W = s * g, Y = i * g, z = c * g, H = m ? "" : `animation: beam-hue-shift-${e} 12s ease-in-out infinite;`, $ = m ? "" : `
@keyframes beam-hue-shift-${e} {
  0% { filter: hue-rotate(calc(var(--beam-hue-base, 0deg) - ${d}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
  50% { filter: hue-rotate(calc(var(--beam-hue-base, 0deg) + ${d}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
  100% { filter: hue-rotate(calc(var(--beam-hue-base, 0deg) - ${d}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
}`, w = k === "dark", y = w ? `conic-gradient(
        from var(--beam-angle-${e}),
        transparent 0%, transparent 54%,
        rgba(255, 255, 255, 0.1) 57%,
        rgba(255, 255, 255, 0.3) 60%,
        rgba(255, 255, 255, 0.6) 63%,
        rgba(255, 255, 255, 0.75) 66%,
        rgba(255, 255, 255, 0.6) 69%,
        rgba(255, 255, 255, 0.3) 72%,
        rgba(255, 255, 255, 0.1) 75%,
        transparent 78%, transparent 100%
      )` : `conic-gradient(
        from var(--beam-angle-${e}),
        transparent 0%, transparent 54%,
        rgba(0, 0, 0, 0.08) 57%,
        rgba(0, 0, 0, 0.2) 60%,
        rgba(0, 0, 0, 0.4) 63%,
        rgba(0, 0, 0, 0.55) 66%,
        rgba(0, 0, 0, 0.4) 69%,
        rgba(0, 0, 0, 0.2) 72%,
        rgba(0, 0, 0, 0.08) 75%,
        transparent 78%, transparent 100%
      )`, x = Ee(b), X = Ae(b), u = w ? `conic-gradient(
        from var(--beam-angle-${e}),
        transparent 0%, transparent 58%,
        rgba(255, 255, 255, 0.03) 62%,
        rgba(255, 255, 255, 0.08) 65%,
        rgba(255, 255, 255, 0.2) 67%,
        rgba(255, 255, 255, 0.45) 69%,
        rgba(255, 255, 255, 0.85) 70%,
        rgba(255, 255, 255, 0.85) 70.5%,
        rgba(255, 255, 255, 0.45) 71.5%,
        rgba(255, 255, 255, 0.2) 73%,
        rgba(255, 255, 255, 0.08) 75%,
        rgba(255, 255, 255, 0.03) 78%,
        transparent 82%
      )` : `conic-gradient(
        from var(--beam-angle-${e}),
        transparent 0%, transparent 58%,
        rgba(0, 0, 0, 0.02) 62%,
        rgba(0, 0, 0, 0.08) 65%,
        rgba(0, 0, 0, 0.2) 67%,
        rgba(0, 0, 0, 0.4) 69%,
        rgba(0, 0, 0, 0.6) 70%,
        rgba(0, 0, 0, 0.6) 70.5%,
        rgba(0, 0, 0, 0.4) 71.5%,
        rgba(0, 0, 0, 0.2) 73%,
        rgba(0, 0, 0, 0.08) 75%,
        rgba(0, 0, 0, 0.02) 78%,
        transparent 82%
      )`;
  return `
@property --beam-angle-${e} {
  syntax: "<angle>";
  initial-value: 0deg;
  inherits: true;
}

@property --beam-opacity-${e} {
  syntax: "<number>";
  initial-value: 0;
  inherits: true;
}

[data-beam="${e}"] {
  position: relative;
  border-radius: ${a}px;
  overflow: hidden;
}

[data-beam="${e}"][data-active] {
  animation:
    beam-spin-${e} ${o}s linear infinite,
    beam-fade-in-${e} 0.6s ease forwards;
}

[data-beam="${e}"][data-fading] {
  animation:
    beam-spin-${e} ${o}s linear infinite,
    beam-fade-out-${e} 0.5s ease forwards;
}

[data-beam="${e}"][data-active]::after,
[data-beam="${e}"][data-fading]::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${f}px;
  padding: ${r}px;
  clip-path: inset(0 round ${a}px);
  background: ${y},${x};
  -webkit-mask:
    conic-gradient(
      from var(--beam-angle-${e}),
      transparent 0%, transparent 30%,
      rgba(255, 255, 255, 0.1) 36%, rgba(255, 255, 255, 0.35) 44%,
      white 52%, white 80%,
      rgba(255, 255, 255, 0.35) 86%, rgba(255, 255, 255, 0.1) 92%,
      transparent 95%, transparent 100%
    ),
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: source-in, xor;
  mask:
    conic-gradient(
      from var(--beam-angle-${e}),
      transparent 0%, transparent 30%,
      rgba(255, 255, 255, 0.1) 36%, rgba(255, 255, 255, 0.35) 44%,
      white 52%, white 80%,
      rgba(255, 255, 255, 0.35) 86%, rgba(255, 255, 255, 0.1) 92%,
      transparent 95%, transparent 100%
    ),
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: intersect, exclude;
  pointer-events: none;
  z-index: 2;
  opacity: calc(var(--beam-opacity-${e}) * ${W.toFixed(2)} * var(--beam-stroke-opacity, 1) * var(--beam-strength, 1));
  ${H}
}

[data-beam="${e}"][data-active]::before,
[data-beam="${e}"][data-fading]::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${a}px;
  background: ${X};
  box-shadow: inset 0 0 9px 1px ${p};
  -webkit-mask-image:
    conic-gradient(
      from var(--beam-angle-${e}),
      transparent 0%, transparent 30%,
      rgba(255, 255, 255, 0.1) 36%, rgba(255, 255, 255, 0.35) 44%,
      white 52%, white 80%,
      rgba(255, 255, 255, 0.35) 86%, rgba(255, 255, 255, 0.1) 92%,
      transparent 95%, transparent 100%
    ),
    linear-gradient(white, transparent 28px, transparent calc(100% - 28px), white),
    linear-gradient(to right, white, transparent 28px, transparent calc(100% - 28px), white);
  -webkit-mask-composite: source-in, source-over;
  mask-image:
    conic-gradient(
      from var(--beam-angle-${e}),
      transparent 0%, transparent 30%,
      rgba(255, 255, 255, 0.1) 36%, rgba(255, 255, 255, 0.35) 44%,
      white 52%, white 80%,
      rgba(255, 255, 255, 0.35) 86%, rgba(255, 255, 255, 0.1) 92%,
      transparent 95%, transparent 100%
    ),
    linear-gradient(white, transparent 28px, transparent calc(100% - 28px), white),
    linear-gradient(to right, white, transparent 28px, transparent calc(100% - 28px), white);
  mask-composite: intersect, add;
  pointer-events: none;
  z-index: 1;
  opacity: calc(var(--beam-opacity-${e}) * ${Y.toFixed(2)} * var(--beam-inner-opacity, 1) * var(--beam-strength, 1));
  clip-path: inset(0 round ${a}px);
  ${H}
}

[data-beam="${e}"] [data-beam-bloom] {
  display: none;
  position: absolute;
  inset: 0;
  border-radius: ${f}px;
  clip-path: inset(0 round ${a}px);
  background: ${u};
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  padding: ${r}px;
  filter: blur(8px) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)});
  pointer-events: none;
  z-index: 3;
  opacity: 0;
}

[data-beam="${e}"][data-active] [data-beam-bloom],
[data-beam="${e}"][data-fading] [data-beam-bloom] {
  display: block;
  opacity: calc(var(--beam-opacity-${e}) * ${z.toFixed(2)} * var(--beam-bloom-opacity, 1) * var(--beam-strength, 1));
}

@keyframes beam-spin-${e} {
  to { --beam-angle-${e}: 360deg; }
}

@keyframes beam-fade-in-${e} {
  to { --beam-opacity-${e}: 1; }
}

@keyframes beam-fade-out-${e} {
  from { --beam-opacity-${e}: 1; }
  to { --beam-opacity-${e}: 0; }
}
${$}
${_(e)}
`;
}
function na(t) {
  const {
    id: e,
    borderRadius: a,
    borderWidth: r,
    duration: o,
    strokeOpacity: s,
    innerOpacity: i,
    bloomOpacity: c,
    colorVariant: p,
    staticColors: b,
    brightness: m,
    saturation: n,
    hueRange: l,
    theme: d
  } = t, k = d === "dark", f = p === "mono" ? 0.5 : 1, g = (s * f).toFixed(2), W = (i * f).toFixed(2), Y = (c * f).toFixed(2), { op: z } = pe("pulse-inner", d, o), H = 8, $ = m.toFixed(2), w = n.toFixed(2), y = b ? `filter: brightness(${$}) saturate(${w});` : `filter: hue-rotate(calc(var(--beam-hue-base, 0deg) + var(--beam-hue-${e}))) brightness(${$}) saturate(${w});`, x = b ? `filter: blur(${H}px) brightness(${$}) saturate(${w});` : `filter: blur(${H}px) hue-rotate(calc(var(--beam-hue-base, 0deg) + var(--beam-hue-${e}))) brightness(${$}) saturate(${w});`, X = ea(p, e), u = aa(p, e, k), v = Ye(Qe, p, 1 - z * 0.5);
  return `
${Oe(e)}

[data-beam="${e}"] {
  position: relative;
  border-radius: ${a}px;
  overflow: hidden;
  isolation: isolate;
}

[data-beam="${e}"][data-active] {
${Q(e, "beam-fade-in", 0.6)}
}

[data-beam="${e}"][data-fading] {
${Q(e, "beam-fade-out", 0.5)}
}

[data-beam="${e}"][data-active]::after,
[data-beam="${e}"][data-fading]::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${a}px;
  padding: ${r}px;
  clip-path: inset(0 round ${a}px);
  background: ${X};
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  pointer-events: none;
  z-index: 2;
  will-change: opacity, filter;
  opacity: calc(var(--beam-opacity-${e}) * ${g} * var(--beam-stroke-opacity, 1) * var(--beam-strength, 1));
  ${y}
}

[data-beam="${e}"][data-active]::before,
[data-beam="${e}"][data-fading]::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${a}px;
  clip-path: inset(0 round ${a}px);
  background: ${u};
  -webkit-mask-image:
    linear-gradient(white, transparent 28px, transparent calc(100% - 28px), white),
    linear-gradient(to right, white, transparent 28px, transparent calc(100% - 28px), white);
  -webkit-mask-composite: source-over;
  mask-image:
    linear-gradient(white, transparent 28px, transparent calc(100% - 28px), white),
    linear-gradient(to right, white, transparent 28px, transparent calc(100% - 28px), white);
  mask-composite: add;
  pointer-events: none;
  z-index: 1;
  will-change: opacity, filter;
  opacity: calc(var(--beam-opacity-${e}) * ${W} * var(--beam-inner-opacity, 1) * var(--beam-strength, 1));
  ${y}
}

[data-beam="${e}"] [data-beam-bloom] {
  display: none;
  position: absolute;
  inset: 0;
  border-radius: ${a}px;
  clip-path: inset(0 round ${a}px);
  background: ${v};
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  padding: ${r}px;
  pointer-events: none;
  z-index: 3;
  will-change: opacity;
  opacity: 0;
}

[data-beam="${e}"][data-active] [data-beam-bloom],
[data-beam="${e}"][data-fading] [data-beam-bloom] {
  display: block;
  opacity: calc(var(--beam-opacity-${e}) * ${Y} * var(--beam-bloom-opacity, 1) * var(--beam-strength, 1));
  ${x}
}

@keyframes beam-fade-in-${e} { to { --beam-opacity-${e}: 1; } }
@keyframes beam-fade-out-${e} { from { --beam-opacity-${e}: 1; } to { --beam-opacity-${e}: 0; } }
${_(e)}

@media (prefers-reduced-motion: reduce) {
  [data-beam="${e}"][data-active],
  [data-beam="${e}"][data-fading],
  [data-beam="${e}"][data-active]::after,
  [data-beam="${e}"][data-fading]::after,
  [data-beam="${e}"][data-active]::before,
  [data-beam="${e}"][data-fading]::before,
  [data-beam="${e}"][data-active] [data-beam-bloom],
  [data-beam="${e}"][data-fading] [data-beam-bloom] {
    animation: none !important;
  }
}
`;
}
function ca(t) {
  const {
    id: e,
    borderRadius: a,
    duration: r,
    strokeOpacity: o,
    innerOpacity: s,
    bloomOpacity: i,
    colorVariant: c,
    staticColors: p,
    brightness: b,
    saturation: m,
    hueRange: n,
    theme: l,
    hairlineOpacity: d = 0
  } = t, k = l === "dark", f = c === "mono" ? 0.5 : 1, g = (o * f).toFixed(2), W = (s * f).toFixed(2), Y = (i * f).toFixed(2), z = k ? "70, 70, 70" : "0, 0, 0", H = d.toFixed(2), $ = `linear-gradient(rgba(${z}, ${H}), rgba(${z}, ${H}))`, { op: w } = pe("pulse-outside", l, r), y = 0.95, x = 0.9, X = k ? 3 : 6, u = k ? 22.5 : 15, v = b.toFixed(2), S = m.toFixed(2), J = p ? `filter: brightness(${v}) saturate(${S});` : `filter: hue-rotate(calc(var(--beam-hue-base, 0deg) + var(--beam-hue-${e}))) brightness(${v}) saturate(${S});`, G = `brightness(var(--beam-glow-brightness, ${v})) saturate(var(--beam-glow-saturate, ${S}))`, ee = p ? `filter: blur(var(--beam-core-blur, ${X}px)) ${G};` : `filter: blur(var(--beam-core-blur, ${X}px)) hue-rotate(calc(var(--beam-hue-base, 0deg) + var(--beam-hue-${e}))) ${G};`, j = p ? `filter: blur(var(--beam-bloom-blur, ${u}px)) ${G};` : `filter: blur(var(--beam-bloom-blur, ${u}px)) hue-rotate(calc(var(--beam-hue-base, 0deg) + var(--beam-hue-${e}))) ${G};`, A = we(ke, c, e), ae = we(ke, c, e), R = Ye(Ze, c, 1 - w * 0.5), O = d > 0 ? `${A},
    ${$}` : A;
  return `
${Oe(e)}

[data-beam="${e}"] {
  position: relative;
  border-radius: ${a}px;
  overflow: visible;
  isolation: isolate;
}

[data-beam="${e}"][data-active] {
${Q(e, "beam-fade-in", 0.6)}
}

[data-beam="${e}"][data-fading] {
${Q(e, "beam-fade-out", 0.5)}
}
${d > 0 ? `
/* Idle hairline — painted above the (opaque) child in the inner 1px edge ring so
   it overlaps a standard inset component border exactly. */
[data-beam="${e}"]::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${a}px;
  padding: 1px;
  clip-path: inset(0 round ${a}px);
  background: ${$};
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  pointer-events: none;
  z-index: 2;
}
` : ""}
[data-beam="${e}"][data-active]::after,
[data-beam="${e}"][data-fading]::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${a}px;
  padding: 1px;
  clip-path: inset(0 round ${a}px);
  background: ${O};
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  mask-composite: exclude;
  pointer-events: none;
  z-index: 2;
  will-change: opacity, filter;
  opacity: calc(var(--beam-opacity-${e}) * ${g} * var(--beam-stroke-opacity, 1) * var(--beam-strength, 1));
  ${J}
}

[data-beam="${e}"][data-active]::before,
[data-beam="${e}"][data-fading]::before {
  content: "";
  position: absolute;
  inset: -10px;
  z-index: -1;
  border-radius: ${a + 10}px;
  background: ${ae};
  transform: scale(${y}, ${x});
  pointer-events: none;
  will-change: opacity, filter;
  opacity: calc(var(--beam-opacity-${e}) * ${W} * var(--beam-inner-opacity, 1) * var(--beam-strength, 1));
  ${ee}
}

[data-beam="${e}"] [data-beam-bloom] {
  display: none;
  position: absolute;
  inset: -30px;
  z-index: -1;
  border-radius: ${a + 30}px;
  background: ${R};
  transform: scale(${y}, ${x});
  pointer-events: none;
  will-change: transform;
  opacity: 0;
}

[data-beam="${e}"][data-active] [data-beam-bloom],
[data-beam="${e}"][data-fading] [data-beam-bloom] {
  display: block;
  opacity: calc(var(--beam-opacity-${e}) * ${Y} * var(--beam-bloom-opacity, 1) * var(--beam-strength, 1));
  ${j}
}

@keyframes beam-fade-in-${e} { to { --beam-opacity-${e}: 1; } }
@keyframes beam-fade-out-${e} { from { --beam-opacity-${e}: 1; } to { --beam-opacity-${e}: 0; } }
${_(e)}

@media (prefers-reduced-motion: reduce) {
  [data-beam="${e}"][data-active],
  [data-beam="${e}"][data-fading],
  [data-beam="${e}"][data-active]::after,
  [data-beam="${e}"][data-fading]::after,
  [data-beam="${e}"][data-active]::before,
  [data-beam="${e}"][data-fading]::before,
  [data-beam="${e}"][data-active] [data-beam-bloom],
  [data-beam="${e}"][data-fading] [data-beam-bloom] {
    animation: none !important;
  }
}
`;
}
function ba(t) {
  const {
    id: e,
    borderRadius: a,
    borderWidth: r,
    duration: o,
    strokeOpacity: s,
    innerOpacity: i,
    bloomOpacity: c,
    innerShadow: p,
    colorVariant: b,
    staticColors: m,
    brightness: n,
    saturation: l,
    hueRange: d,
    theme: k
  } = t, f = Math.max(0, a - r), g = k === "dark", W = s, Y = i, z = c, H = m ? "" : `animation: beam-hue-shift-${e} 12s ease-in-out infinite;`, $ = m ? "" : `animation: beam-hue-shift-bloom-${e} 8s ease-in-out infinite;`, w = m ? "" : `
@keyframes beam-hue-shift-${e} {
  0% { filter: hue-rotate(calc(var(--beam-hue-base, 0deg) - ${d}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
  50% { filter: hue-rotate(calc(var(--beam-hue-base, 0deg) + ${d}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
  100% { filter: hue-rotate(calc(var(--beam-hue-base, 0deg) - ${d}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
}

@keyframes beam-hue-shift-bloom-${e} {
  0% { filter: blur(8px) hue-rotate(calc(var(--beam-hue-base, 0deg) - ${d + 10}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
  50% { filter: blur(8px) hue-rotate(calc(var(--beam-hue-base, 0deg) + ${d + 10}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
  100% { filter: blur(8px) hue-rotate(calc(var(--beam-hue-base, 0deg) - ${d + 10}deg)) brightness(${n.toFixed(2)}) saturate(${l.toFixed(2)}); }
}`, y = g ? `radial-gradient(
        ellipse calc(24px * var(--beam-w-${e})) calc(28px * var(--beam-h-${e})) at calc(var(--beam-x-${e}) * 100%) calc(100% + 2px),
        rgba(255, 255, 255, 0.38) 0%,
        rgba(255, 255, 255, 0.12) 30%,
        transparent 65%
      )` : `radial-gradient(
        ellipse calc(35px * var(--beam-w-${e})) calc(28px * var(--beam-h-${e})) at calc(var(--beam-x-${e}) * 100%) calc(100% + 2px),
        rgba(0, 0, 0, 0.6) 0%,
        rgba(0, 0, 0, 0.25) 35%,
        transparent 70%
      )`, x = Te(b, g, e), X = Ve(b, e), u = Ue(b, g, e), v = b === "mono" ? "filter: blur(6px);" : "";
  return `
@property --beam-x-${e} {
  syntax: "<number>";
  initial-value: 0;
  inherits: true;
}

@property --beam-w-${e} {
  syntax: "<number>";
  initial-value: 1;
  inherits: true;
}

@property --beam-h-${e} {
  syntax: "<number>";
  initial-value: 1;
  inherits: true;
}

@property --beam-spike-${e} {
  syntax: "<number>";
  initial-value: 1;
  inherits: true;
}

@property --beam-spike2-${e} {
  syntax: "<number>";
  initial-value: 1;
  inherits: true;
}

@property --beam-edge-${e} {
  syntax: "<number>";
  initial-value: 1;
  inherits: true;
}

@property --beam-opacity-${e} {
  syntax: "<number>";
  initial-value: 0;
  inherits: true;
}

[data-beam="${e}"] {
  position: relative;
  border-radius: ${a}px;
  overflow: hidden;
}

[data-beam="${e}"][data-active] {
  animation:
    beam-travel-${e} ${o}s linear infinite,
    beam-edge-fade-${e} ${o}s linear infinite,
    beam-breathe-${e} ${(o * 1.3).toFixed(1)}s ease-in-out infinite,
    beam-spike-${e} ${(o * 1.33).toFixed(1)}s ease-in-out infinite,
    beam-spike2-${e} ${(o * 1.7).toFixed(1)}s ease-in-out infinite,
    beam-fade-in-${e} 0.6s ease forwards;
}

[data-beam="${e}"][data-fading] {
  animation:
    beam-travel-${e} ${o}s linear infinite,
    beam-edge-fade-${e} ${o}s linear infinite,
    beam-breathe-${e} ${(o * 1.3).toFixed(1)}s ease-in-out infinite,
    beam-spike-${e} ${(o * 1.33).toFixed(1)}s ease-in-out infinite,
    beam-spike2-${e} ${(o * 1.7).toFixed(1)}s ease-in-out infinite,
    beam-fade-out-${e} 0.5s ease forwards;
}

[data-beam="${e}"][data-active]::after,
[data-beam="${e}"][data-fading]::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${f}px;
  padding: ${r}px;
  clip-path: inset(0 round ${a}px);
  background: ${y}, ${x};
  -webkit-mask:
    radial-gradient(
      ellipse calc(78px * var(--beam-w-${e})) calc(60px * var(--beam-h-${e})) at calc(var(--beam-x-${e}) * 100%) 100%,
      white 0%, rgba(255, 255, 255, 0.5) 45%, transparent 100%
    ),
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: source-in, xor;
  mask:
    radial-gradient(
      ellipse calc(78px * var(--beam-w-${e})) calc(60px * var(--beam-h-${e})) at calc(var(--beam-x-${e}) * 100%) 100%,
      white 0%, rgba(255, 255, 255, 0.5) 45%, transparent 100%
    ),
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask-composite: intersect, exclude;
  pointer-events: none;
  z-index: 2;
  opacity: calc(var(--beam-opacity-${e}) * var(--beam-edge-${e}) * ${W.toFixed(2)} * var(--beam-stroke-opacity, 1) * var(--beam-strength, 1));
  ${H}
}

[data-beam="${e}"][data-active]::before,
[data-beam="${e}"][data-fading]::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: ${a}px;
  background: ${X};
  box-shadow: inset 0 0 9px 1px ${p};
  -webkit-mask-image:
    radial-gradient(
      ellipse calc(78px * var(--beam-w-${e})) calc(60px * var(--beam-h-${e})) at calc(var(--beam-x-${e}) * 100%) 100%,
      white 0%, rgba(255, 255, 255, 0.5) 45%, transparent 100%
    ),
    linear-gradient(white, transparent 28px, transparent calc(100% - 28px), white),
    linear-gradient(to right, white, transparent 28px, transparent calc(100% - 28px), white);
  -webkit-mask-composite: source-in, source-over;
  mask-image:
    radial-gradient(
      ellipse calc(78px * var(--beam-w-${e})) calc(60px * var(--beam-h-${e})) at calc(var(--beam-x-${e}) * 100%) 100%,
      white 0%, rgba(255, 255, 255, 0.5) 45%, transparent 100%
    ),
    linear-gradient(white, transparent 28px, transparent calc(100% - 28px), white),
    linear-gradient(to right, white, transparent 28px, transparent calc(100% - 28px), white);
  mask-composite: intersect, add;
  pointer-events: none;
  z-index: 1;
  opacity: calc(var(--beam-opacity-${e}) * var(--beam-edge-${e}) * ${Y.toFixed(2)} * var(--beam-inner-opacity, 1) * var(--beam-strength, 1));
  clip-path: inset(0 round ${a}px);
  ${H}
}

[data-beam="${e}"] [data-beam-bloom] {
  display: none;
  position: absolute;
  inset: 0;
  border-radius: ${f}px;
  clip-path: inset(0 round ${a}px);
  padding: 0;
  -webkit-mask: radial-gradient(
    ellipse calc(84px * var(--beam-w-${e})) calc(110px * var(--beam-h-${e})) at calc(var(--beam-x-${e}) * 100%) 100%,
    white 0%, rgba(255, 255, 255, 0.5) 35%, transparent 100%
  );
  -webkit-mask-composite: source-over;
  mask: radial-gradient(
    ellipse calc(84px * var(--beam-w-${e})) calc(110px * var(--beam-h-${e})) at calc(var(--beam-x-${e}) * 100%) 100%,
    white 0%, rgba(255, 255, 255, 0.5) 35%, transparent 100%
  );
  mask-composite: add;
  background: ${u};
  ${v}
  pointer-events: none;
  z-index: 3;
  opacity: 0;
}

[data-beam="${e}"][data-active] [data-beam-bloom],
[data-beam="${e}"][data-fading] [data-beam-bloom] {
  display: block;
  opacity: calc(var(--beam-opacity-${e}) * var(--beam-edge-${e}) * ${z.toFixed(2)} * var(--beam-bloom-opacity, 1) * var(--beam-strength, 1));
  ${$}
}

@keyframes beam-travel-${e} {
  0%   { --beam-x-${e}: 0.06;  --beam-w-${e}: 0.5; }
  10%  { --beam-x-${e}: 0.15;  --beam-w-${e}: 0.8; }
  20%  { --beam-x-${e}: 0.25;  --beam-w-${e}: 1.1; }
  30%  { --beam-x-${e}: 0.35;  --beam-w-${e}: 1.3; }
  40%  { --beam-x-${e}: 0.44;  --beam-w-${e}: 1.45; }
  50%  { --beam-x-${e}: 0.5;   --beam-w-${e}: 1.5; }
  60%  { --beam-x-${e}: 0.56;  --beam-w-${e}: 1.45; }
  70%  { --beam-x-${e}: 0.65;  --beam-w-${e}: 1.3; }
  80%  { --beam-x-${e}: 0.75;  --beam-w-${e}: 1.1; }
  90%  { --beam-x-${e}: 0.85;  --beam-w-${e}: 0.8; }
  100% { --beam-x-${e}: 0.94;  --beam-w-${e}: 0.5; }
}

@keyframes beam-edge-fade-${e} {
  0%    { --beam-edge-${e}: 0; }
  12.5% { --beam-edge-${e}: 0; }
  32.5% { --beam-edge-${e}: 1; }
  67.5% { --beam-edge-${e}: 1; }
  87.5% { --beam-edge-${e}: 0; }
  100%  { --beam-edge-${e}: 0; }
}

@keyframes beam-breathe-${e} {
  0%, 100% { --beam-h-${e}: 0.8; }
  25%      { --beam-h-${e}: 1.25; }
  55%      { --beam-h-${e}: 0.85; }
  80%      { --beam-h-${e}: 1.3; }
}

@keyframes beam-spike-${e} {
  0%   { --beam-spike-${e}: 0.8; }
  25%  { --beam-spike-${e}: 1.3; }
  50%  { --beam-spike-${e}: 0.9; }
  75%  { --beam-spike-${e}: 1.4; }
  100% { --beam-spike-${e}: 0.8; }
}

@keyframes beam-spike2-${e} {
  0%   { --beam-spike2-${e}: 1.2; }
  25%  { --beam-spike2-${e}: 0.7; }
  50%  { --beam-spike2-${e}: 1.4; }
  75%  { --beam-spike2-${e}: 0.8; }
  100% { --beam-spike2-${e}: 1.2; }
}

@keyframes beam-fade-in-${e} {
  to { --beam-opacity-${e}: 1; }
}

@keyframes beam-fade-out-${e} {
  from { --beam-opacity-${e}: 1; }
  to { --beam-opacity-${e}: 0; }
}
${w}
${_(e)}
`;
}
const Z = /* @__PURE__ */ new Set();
let E = null, ce = 0;
const pa = 1e3 / 30 - 2, la = Math.PI * 2;
function We(t) {
  return (1 - Math.cos(la * t)) / 2;
}
function Fe(t) {
  if (E = requestAnimationFrame(Fe), t - ce < pa) return;
  ce = t;
  const e = t / 1e3;
  Z.forEach(({ el: a, config: r }) => {
    for (const o of r.oscillators) {
      const s = (e - o.delay) / o.period, i = o.a + (o.b - o.a) * We(s);
      a.style.setProperty(
        o.prop,
        o.unit === "px" ? `${i.toFixed(2)}px` : i.toFixed(4)
      );
    }
    if (r.hue) {
      const { prop: o, range: s, period: i, continuous: c } = r.hue, p = c ? e / i % 1 * s : -s + 2 * s * We(e / i);
      a.style.setProperty(o, `${p.toFixed(2)}deg`);
    }
  });
}
function da() {
  E == null && (ce = 0, E = requestAnimationFrame(Fe));
}
function fa() {
  Z.size === 0 && E != null && (cancelAnimationFrame(E), E = null);
}
function ga(t, e) {
  const a = { el: t, config: e };
  return Z.add(a), da(), () => {
    Z.delete(a), fa();
  };
}
function ma() {
  const [t, e] = P(() => typeof window > "u" || window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  return B(() => {
    if (typeof window > "u") return;
    const a = window.matchMedia("(prefers-color-scheme: dark)"), r = (o) => {
      e(o.matches ? "dark" : "light");
    };
    return a.addEventListener("change", r), () => a.removeEventListener("change", r);
  }, []), t;
}
function $a(t, e) {
  return t === "auto" ? e : t;
}
const za = Ge(
  function({
    children: e,
    size: a = "md",
    colorVariant: r = "colorful",
    theme: o = "dark",
    staticColors: s = !1,
    duration: i,
    active: c = !0,
    borderRadius: p,
    brightness: b,
    saturation: m,
    hueRange: n = 30,
    strength: l = 1,
    className: d,
    style: k,
    onActivate: f,
    onDeactivate: g,
    onAnimationEnd: W,
    ...Y
  }, z) {
    const $ = Me().replace(/:/g, "-"), w = ma(), y = Ie(null), [x, X] = P(c), [u, v] = P(!1), [S, J] = P(!0), [G, ee] = P(null), [j, A] = P({ x: 1, y: 1 });
    B(() => {
      if (p != null) return;
      const h = y.current;
      if (!h) return;
      const F = () => {
        const I = h.firstElementChild;
        if (!I) return;
        const se = getComputedStyle(I), L = parseFloat(se.borderTopLeftRadius);
        !isNaN(L) && L > 0 && ee(L);
      };
      F();
      const M = new MutationObserver(F);
      return M.observe(h, { childList: !0, subtree: !1 }), () => M.disconnect();
    }, [p, e]), B(() => {
      c && !x && !u ? X(!0) : !c && x && !u && v(!0);
    }, [c, x, u]), B(() => {
      const h = y.current;
      if (!h || typeof IntersectionObserver > "u") return;
      const F = new IntersectionObserver(
        (M) => {
          for (const I of M) J(I.isIntersecting);
        },
        // Start animating slightly before the element scrolls into view.
        { rootMargin: "256px" }
      );
      return F.observe(h), () => F.disconnect();
    }, []), B(() => {
      if (a !== "pulse-outside") {
        A({ x: 1, y: 1 });
        return;
      }
      const h = y.current;
      if (!h) return;
      const F = 350, M = 140, I = 0.35, se = 4, L = (D) => Math.max(I, Math.min(se, D)), ge = () => {
        const D = h.firstElementChild;
        if (!D) return;
        const U = D.getBoundingClientRect();
        if (!U.width || !U.height) return;
        const ue = +L(U.width / F).toFixed(3), xe = +L(U.height / M).toFixed(3);
        A((ie) => ie.x === ue && ie.y === xe ? ie : { x: ue, y: xe });
      };
      if (ge(), typeof ResizeObserver > "u") return;
      const me = h.firstElementChild;
      if (!me) return;
      const $e = new ResizeObserver(ge);
      return $e.observe(me), () => $e.disconnect();
    }, [a, e]);
    const ae = ye(
      (h) => {
        const F = h.animationName;
        F.includes("fade-out") ? (X(!1), v(!1), g == null || g()) : F.includes("fade-in") && (f == null || f()), W == null || W(h);
      },
      [f, g, W]
    ), R = $a(o, w), O = ne[a][R], re = Le[a], te = a === "pulse-inner" || a === "pulse-outside", le = p ?? G ?? re.borderRadius, T = i ?? (a === "line" ? 3.1 : te ? 2.3 : 1.96), de = m ?? O.saturation, fe = b ?? O.brightness ?? 1.3, N = a === "line" ? Math.min(n, 13) : n, V = r === "mono" ? !0 : s, Se = ve(
      () => oa({
        id: $,
        borderRadius: le,
        borderWidth: re.borderWidth,
        duration: T,
        strokeOpacity: O.strokeOpacity,
        innerOpacity: O.innerOpacity,
        bloomOpacity: O.bloomOpacity,
        innerShadow: O.innerShadow,
        size: a,
        colorVariant: r,
        staticColors: V,
        brightness: fe,
        saturation: de,
        hueRange: N,
        theme: R,
        hairlineOpacity: O.hairlineOpacity
      }),
      [
        $,
        le,
        re.borderWidth,
        T,
        O.strokeOpacity,
        O.innerOpacity,
        O.bloomOpacity,
        O.innerShadow,
        O.hairlineOpacity,
        a,
        r,
        V,
        fe,
        de,
        N,
        R
      ]
    ), oe = ve(
      () => te ? ta(a, R, T, N, V, $) : null,
      [te, a, R, T, N, V, $]
    );
    B(() => {
      var F;
      if (!oe || !(x || u) || !S) return;
      const h = y.current;
      if (h && !(typeof window < "u" && ((F = window.matchMedia) != null && F.call(window, "(prefers-reduced-motion: reduce)").matches)))
        return ga(h, oe);
    }, [oe, x, u, S]);
    const Re = ye(
      (h) => {
        y.current = h, typeof z == "function" ? z(h) : z && (z.current = h);
      },
      [z]
    ), qe = {
      ...k ?? {},
      "--beam-strength": Math.max(0, Math.min(1, l)),
      ...a === "pulse-outside" ? { "--pulse-glow-sx": j.x, "--pulse-glow-sy": j.y } : {}
    };
    return /* @__PURE__ */ he(Ce, { children: [
      /* @__PURE__ */ ze("style", { children: Se }),
      /* @__PURE__ */ he(
        "div",
        {
          ...Y,
          ref: Re,
          "data-beam": $,
          "data-active": x && !u ? "" : void 0,
          "data-fading": u ? "" : void 0,
          "data-paused": x && !u && !S ? "" : void 0,
          className: d,
          style: qe,
          onAnimationEnd: ae,
          children: [
            e,
            /* @__PURE__ */ ze("div", { "data-beam-bloom": !0 })
          ]
        }
      )
    ] });
  }
);
export {
  za as BorderBeam,
  za as default,
  Le as sizePresets,
  ne as sizeThemePresets,
  ha as themeColors
};
