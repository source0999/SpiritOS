import { describe, expect, it } from "vitest";
import {
  normalizeWindowsPhysicalDiskType,
  _constants,
} from "./windows-drive-type.js";

describe("normalizeWindowsPhysicalDiskType (Windows agent → DriveType union)", () => {
  it("maps NVMe bus strings + enum int to NVME", () => {
    expect(normalizeWindowsPhysicalDiskType("NVMe", null, null)).toBe("NVME");
    expect(normalizeWindowsPhysicalDiskType("nvme", "Unspecified", null)).toBe(
      "NVME",
    );
    expect(normalizeWindowsPhysicalDiskType(_constants.BUS_TYPE_NVME, 0, null)).toBe(
      "NVME",
    );
    expect(normalizeWindowsPhysicalDiskType("17", null, null)).toBe("NVME");
  });

  it("maps SSD / SCM media (strings + WMI ints) to SSD", () => {
    expect(normalizeWindowsPhysicalDiskType("SATA", "SSD", null)).toBe("SSD");
    expect(normalizeWindowsPhysicalDiskType("SATA", "SCM", null)).toBe("SSD");
    expect(
      normalizeWindowsPhysicalDiskType("USB", _constants.MEDIA_SSD, null),
    ).toBe("SSD");
    expect(
      normalizeWindowsPhysicalDiskType("ATA", _constants.MEDIA_SCM, null),
    ).toBe("SSD");
  });

  it("maps HDD media to HDD", () => {
    expect(normalizeWindowsPhysicalDiskType("SATA", "HDD", null)).toBe("HDD");
    expect(
      normalizeWindowsPhysicalDiskType("USB", _constants.MEDIA_HDD, null),
    ).toBe("HDD");
  });

  it("returns UNKNOWN when media is unspecified / blank / ambiguous", () => {
    expect(normalizeWindowsPhysicalDiskType("SATA", "Unspecified", null)).toBe(
      "UNKNOWN",
    );
    expect(normalizeWindowsPhysicalDiskType("SATA", null, null)).toBe("UNKNOWN");
    expect(normalizeWindowsPhysicalDiskType(null, "", null)).toBe("UNKNOWN");
    expect(
      normalizeWindowsPhysicalDiskType(
        "USB",
        _constants.MEDIA_UNSPECIFIED,
        null,
      ),
    ).toBe("UNKNOWN");
  });

  it("uses SpindleSpeed when MediaType is Unspecified (Windows reality)", () => {
    expect(
      normalizeWindowsPhysicalDiskType("SATA", "Unspecified", 0),
    ).toBe("SSD");
    expect(
      normalizeWindowsPhysicalDiskType("SATA", "Unspecified", 7200),
    ).toBe("HDD");
    expect(
      normalizeWindowsPhysicalDiskType("USB", "Unspecified", 0),
    ).toBe("UNKNOWN");
  });
});

/** Representative shapes from agent.js after PowerShell JSON.parse */
describe("Windows agent JSON rows → normalized type", () => {
  it("matches NVME / SSD / HDD / UNKNOWN fixture rows", () => {
    const nvmeRow = {
      PhysicalBusType: "NVMe",
      PhysicalMediaType: "Unspecified",
    };
    const ssdRow = {
      PhysicalBusType: "SATA",
      PhysicalMediaType: "SSD",
    };
    const hddRow = {
      PhysicalBusType: "SATA",
      PhysicalMediaType: "HDD",
    };
    const unknownRow = {
      PhysicalBusType: "SATA",
      PhysicalMediaType: "Unspecified",
    };

    expect(
      normalizeWindowsPhysicalDiskType(
        nvmeRow.PhysicalBusType,
        nvmeRow.PhysicalMediaType,
        null,
      ),
    ).toBe("NVME");
    expect(
      normalizeWindowsPhysicalDiskType(
        ssdRow.PhysicalBusType,
        ssdRow.PhysicalMediaType,
        null,
      ),
    ).toBe("SSD");
    expect(
      normalizeWindowsPhysicalDiskType(
        hddRow.PhysicalBusType,
        hddRow.PhysicalMediaType,
        null,
      ),
    ).toBe("HDD");
    expect(
      normalizeWindowsPhysicalDiskType(
        unknownRow.PhysicalBusType,
        unknownRow.PhysicalMediaType,
        null,
      ),
    ).toBe("UNKNOWN");
  });
});
