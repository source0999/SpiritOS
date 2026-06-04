import { ConverterQueueService } from "@/lib/converter/converterQueueService";

const globalForConverter = globalThis as typeof globalThis & {
  __spiritConverterQueue?: ConverterQueueService;
};

export function getConverterQueue(): ConverterQueueService {
  if (!globalForConverter.__spiritConverterQueue) {
    globalForConverter.__spiritConverterQueue = new ConverterQueueService();
  }

  return globalForConverter.__spiritConverterQueue;
}
