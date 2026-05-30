export default class BasicReporter {
  onFinished(files = [], errors = []) {
    const failedFiles = files.filter((file) => file.result?.state === "fail").length;
    const passedFiles = files.length - failedFiles;
    console.log(`\nBasic reporter: ${passedFiles} passed files, ${failedFiles} failed files, ${errors.length} errors`);
  }
}
