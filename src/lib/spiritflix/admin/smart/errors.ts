export class SpiritFlixSmartProbeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SpiritFlixSmartProbeError";
  }
}

export class SpiritFlixSmartSamplerError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SpiritFlixSmartSamplerError";
  }
}

export class SpiritFlixSmartScannerError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SpiritFlixSmartScannerError";
  }
}
