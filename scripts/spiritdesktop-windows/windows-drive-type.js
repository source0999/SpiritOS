// ── Windows PhysicalDisk → Spirit DriveType ───────────────────────────────────
// Get-PhysicalDisk emits BusType/MediaType as strings via ToString(), but
// ConvertTo-Json sometimes numeric-enums the bastards. Handle both.

/** @typedef {"SSD"|"HDD"|"NVME"|"UNKNOWN"} DriveTypeUnion */

// Microsoft.Management.Infrastructure / Storage BusType (subset used here)
const BUS_TYPE_NVME = 17;

// MSFT_PhysicalDisk MediaType
const MEDIA_UNSPECIFIED = 0;
const MEDIA_HDD = 3;
const MEDIA_SSD = 4;
const MEDIA_SCM = 5;

function parseSpindleRpm(v) {
  if (v === null || v === undefined) return NaN;
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "bigint") return Number(v);
  if (typeof v === "string" && v.trim() !== "") {
    const n = Number(v.trim());
    if (Number.isFinite(n)) return n;
  }
  return NaN;
}

/** SATA-class buses where spindle RPM distinguishes SSD (0) vs HDD (≥4k RPM) when MediaType lies. */
function isFixedDiskBusForSpindleHeuristic(bStr) {
  const b = bStr.toLowerCase();
  return (
    b === "sata" ||
    b === "ata" ||
    b === "sas" ||
    b === "scsi" ||
    b === "raid" ||
    b === "ide"
  );
}

/**
 * Map PhysicalDisk BusType + MediaType (strings or enum ints from JSON) → telemetry union.
 * Optional PhysicalDisk.SpindleSpeed helps when MediaType stays "Unspecified" (runtime-proven gap).
 *
 * @param {string|number|null|undefined} busType
 * @param {string|number|null|undefined} mediaType
 * @param {string|number|bigint|null|undefined} spindleSpeedRpm - Get-PhysicalDisk SpindleSpeed; SSDs → 0, HDDs → RPM
 * @returns {DriveTypeUnion}
 */
function normalizeWindowsPhysicalDiskType(busType, mediaType, spindleSpeedRpm) {
  const bRaw = busType;
  const mRaw = mediaType;

  const bNum =
    typeof bRaw === "number" && Number.isFinite(bRaw)
      ? bRaw
      : typeof bRaw === "string" && bRaw.trim() !== "" && !Number.isNaN(Number(bRaw))
        ? Number(bRaw)
        : NaN;
  const mNum =
    typeof mRaw === "number" && Number.isFinite(mRaw)
      ? mRaw
      : typeof mRaw === "string" && mRaw.trim() !== "" && !Number.isNaN(Number(mRaw))
        ? Number(mRaw)
        : NaN;

  const bStr = String(bRaw ?? "")
    .trim()
    .toLowerCase();
  const mStr = String(mRaw ?? "")
    .trim()
    .toLowerCase();

  // NVMe — bus wins over nonsense media labels
  if (bNum === BUS_TYPE_NVME || bStr === "nvme" || bStr.includes("nvme")) {
    return "NVME";
  }

  // SCM / SSD / HDD from MediaType (string or WMI enum int)
  if (
    mStr === "ssd" ||
    mStr === "scm" ||
    mNum === MEDIA_SSD ||
    mNum === MEDIA_SCM
  ) {
    return "SSD";
  }
  if (mStr === "hdd" || mNum === MEDIA_HDD) {
    return "HDD";
  }

  const rpm = parseSpindleRpm(spindleSpeedRpm);
  // Rotational disks report real RPM; SSD/NVMe report 0. Empirical floor avoids USB noise.
  if (Number.isFinite(rpm) && rpm >= 4000) {
    return "HDD";
  }
  // Internal fixed buses + 0 RPM → typical Microsoft "Unspecified" SSD fingerprint (see debug logs).
  if (rpm === 0 && isFixedDiskBusForSpindleHeuristic(bStr)) {
    return "SSD";
  }

  return "UNKNOWN";
}

module.exports = {
  normalizeWindowsPhysicalDiskType,
  // tests / diagnostics only
  _constants: {
    BUS_TYPE_NVME,
    MEDIA_UNSPECIFIED,
    MEDIA_HDD,
    MEDIA_SSD,
    MEDIA_SCM,
  },
};
