import {
  type ConverterBatchInput,
  type ConverterJob,
  type ConverterQueueSnapshot,
  type ConverterQueueState,
} from "@/lib/converter/converterTypes";
import {
  detectConverterTools,
  parseConverterBatch,
  processConverterJob,
  validateConverterJob,
  type AuthorizedMediaImportOptions,
} from "@/lib/converter/authorizedMediaImportService";

export class ConverterQueueService {
  private jobs: ConverterJob[] = [];
  private state: ConverterQueueState = "idle";
  private activeJobId: string | undefined;
  private processing = false;
  private cancelRequested = false;
  private options: AuthorizedMediaImportOptions;

  constructor(options: AuthorizedMediaImportOptions = {}) {
    this.options = options;
  }

  enqueueBatch(input: ConverterBatchInput): ConverterJob[] {
    const jobs = parseConverterBatch(input, this.options).map(validateConverterJob);
    this.jobs = [...this.jobs, ...jobs];
    return jobs;
  }

  async start(): Promise<void> {
    if (this.processing) {
      return;
    }

    this.cancelRequested = false;
    this.processing = true;
    this.state = "running";

    try {
      const tools = this.options.tools ?? (await detectConverterTools(this.options.commandRunner));
      while ((this.state as ConverterQueueState) !== "cancelled") {
        if ((this.state as ConverterQueueState) === "paused") {
          await delay(50);
          continue;
        }

        const index = this.jobs.findIndex((job) => job.state === "queued");
        if (index === -1) {
          this.state = "idle";
          this.activeJobId = undefined;
          return;
        }

        const job = this.jobs[index];
        this.activeJobId = job.id;
        const processed = await processConverterJob(job, {
          ...this.options,
          tools,
          shouldCancel: () => this.cancelRequested,
        });
        this.jobs[index] = processed;

        if (this.cancelRequested) {
          this.state = "cancelled";
          this.activeJobId = undefined;
          return;
        }
      }
    } finally {
      this.processing = false;
      if ((this.state as ConverterQueueState) !== "paused" && (this.state as ConverterQueueState) !== "cancelled") {
        this.activeJobId = undefined;
      }
    }
  }

  pause(): ConverterQueueSnapshot {
    if (this.state === "running") {
      this.state = "paused";
    }
    return this.snapshot();
  }

  resume(): void {
    if (this.state === "paused") {
      this.state = "running";
      void this.start();
    }
  }

  cancel(): ConverterQueueSnapshot {
    this.cancelRequested = true;
    this.state = "cancelled";
    this.jobs = this.jobs.map((job) =>
      job.state === "queued"
        ? { ...job, state: "cancelled", updatedAt: new Date().toISOString() }
        : job,
    );
    return this.snapshot();
  }

  clear(): ConverterQueueSnapshot {
    if (this.processing) {
      this.cancel();
    }
    this.jobs = [];
    this.activeJobId = undefined;
    this.state = "idle";
    this.cancelRequested = false;
    return this.snapshot();
  }

  snapshot(): ConverterQueueSnapshot {
    return {
      state: this.state,
      activeJobId: this.activeJobId,
      jobs: this.jobs,
    };
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
