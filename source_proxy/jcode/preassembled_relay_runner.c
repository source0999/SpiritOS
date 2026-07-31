/* Proxy-owned static launcher for the C2-J preassembled read-only root. */
#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/prctl.h>
#include <sys/resource.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <unistd.h>

static const char *profile = "spiritos-qualification";
static const char *model = "qwen2.5-coder:7b";

static int write_config(const char *path, const char *base) {
  char config[2048];
  int fd, count;
  if (strncmp(base, "http://127.0.0.1:", 17) || !strstr(base, "/v1")) return -1;
  count = snprintf(config, sizeof(config),
    "[provider]\ndefault_provider = \"%s\"\ndefault_model = \"%s\"\n\n"
    "[providers.%s]\ntype = \"openai-compatible\"\nbase_url = \"%s\"\n"
    "auth = \"none\"\nrequires_api_key = false\nprovider_routing = false\nmodel_catalog = false\n\n"
    "[[providers.%s.models]]\nid = \"%s\"\n", profile, model, profile, base, profile, model);
  if (count < 0 || (size_t)count >= sizeof(config)) return -1;
  fd = open(path, O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) return -1;
  if (write(fd, config, (size_t)count) != count || close(fd) != 0) return -1;
  return 0;
}

static void close_nonstandard_fds(void) {
  struct rlimit lim;
  rlim_t upper = 65536;
  if (getrlimit(RLIMIT_NOFILE, &lim) == 0 && lim.rlim_cur != RLIM_INFINITY) upper = lim.rlim_cur;
  for (int fd = 3; fd < (int)upper; ++fd) close(fd);
}

static void forward_pair(int left, int right) {
  char buffer[65536];
  int left_open = 1, right_open = 1;
  while (left_open || right_open) {
    fd_set readable;
    int high = left > right ? left : right;
    FD_ZERO(&readable);
    if (left_open) FD_SET(left, &readable);
    if (right_open) FD_SET(right, &readable);
    if (select(high + 1, &readable, NULL, NULL, NULL) <= 0) return;
    for (int source_index = 0; source_index < 2; ++source_index) {
      int source = source_index ? right : left;
      int dest = source_index ? left : right;
      ssize_t read_count;
      int *source_open = source_index ? &right_open : &left_open;
      if (!FD_ISSET(source, &readable)) continue;
      read_count = read(source, buffer, sizeof(buffer));
      if (read_count == 0) { shutdown(dest, SHUT_WR); *source_open = 0; continue; }
      if (read_count < 0) return;
      for (ssize_t offset = 0; offset < read_count;) {
        ssize_t written = write(dest, buffer + offset, (size_t)(read_count - offset));
        if (written <= 0) return;
        offset += written;
      }
    }
  }
}

static int write_fixture_content(const char *content, const char *destination, mode_t mode) {
  int output = open(destination, O_WRONLY | O_CREAT | O_EXCL, mode);
  size_t length = strlen(content);
  if (output < 0) return -1;
  if (write(output, content, length) != (ssize_t)length || close(output) || chmod(destination, mode)) return -1;
  return 0;
}

static int prepare_writable_fixture(const char *source_content, const char *test_content) {
  if (!source_content && !test_content) return 0;
  if (!source_content || !test_content) return 1;
  if (mkdir("/tmp/jcode-home/workspace", 0700) && errno != EEXIST) return 2;
  if (mkdir("/tmp/jcode-home/workspace/qualification_write_fixture", 0755) && errno != EEXIST) return 3;
  if (write_fixture_content(source_content, "/tmp/jcode-home/workspace/qualification_write_fixture/source_file.py", 0644)) return 6;
  if (write_fixture_content(test_content, "/tmp/jcode-home/workspace/qualification_write_fixture/test_source_file.py", 0444)) return 7;
  if (chmod("/tmp/jcode-home/workspace/qualification_write_fixture", 0555)) return 8;
  return chdir("/tmp/jcode-home/workspace") ? 9 : 0;
}

static void serve(int listener, const char *socket_path, int relay_fd) {
  for (;;) {
    int client = accept(listener, NULL, NULL);
    struct sockaddr_un address;
    int upstream;
    if (client < 0) { if (errno == EINTR) continue; return; }
    if (relay_fd >= 0) { forward_pair(client, relay_fd); close(client); return; }
    upstream = socket(AF_UNIX, SOCK_STREAM, 0);
    if (upstream < 0) { close(client); continue; }
    memset(&address, 0, sizeof(address)); address.sun_family = AF_UNIX;
    if (strlen(socket_path) >= sizeof(address.sun_path)) { close(client); close(upstream); continue; }
    strcpy(address.sun_path, socket_path);
    if (connect(upstream, (struct sockaddr *)&address, sizeof(address)) == 0) forward_pair(client, upstream);
    close(client); close(upstream);
  }
}

int main(int argc, char **argv) {
  const char *socket_path = NULL, *config_path = NULL, *base_url = NULL;
  const char *source_template = NULL, *test_template = NULL;
  int port = 0, command = -1, listener = -1, relay_fd = -1;
  for (int index = 1; index < argc; ++index) {
    if (!strcmp(argv[index], "--")) { command = index + 1; break; }
    if (!strcmp(argv[index], "--socket") && index + 1 < argc) socket_path = argv[++index];
    else if (!strcmp(argv[index], "--config-path") && index + 1 < argc) config_path = argv[++index];
    else if (!strcmp(argv[index], "--base-url") && index + 1 < argc) base_url = argv[++index];
    else if (!strcmp(argv[index], "--model") && index + 1 < argc) model = argv[++index];
    else if (!strcmp(argv[index], "--fixture-source-content") && index + 1 < argc) source_template = argv[++index];
    else if (!strcmp(argv[index], "--fixture-test-content") && index + 1 < argc) test_template = argv[++index];
    else if (!strcmp(argv[index], "--relay-fd") && index + 1 < argc) relay_fd = atoi(argv[++index]);
    else if (!strcmp(argv[index], "--listen-port") && index + 1 < argc) port = atoi(argv[++index]);
    else return 64;
  }
  if (!config_path || !base_url || command < 0 || command >= argc || write_config(config_path, base_url) != 0) return 65;
  { int prepared = prepare_writable_fixture(source_template, test_template); if (prepared) return 69 + prepared; }
  if (socket_path || relay_fd >= 0) {
    struct sockaddr_in address;
    int one = 1;
    if (port < 1 || port > 65535 || (listener = socket(AF_INET, SOCK_STREAM, 0)) < 0) return 66;
    setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    memset(&address, 0, sizeof(address)); address.sin_family = AF_INET; address.sin_port = htons((unsigned short)port); address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(listener, (struct sockaddr *)&address, sizeof(address)) || listen(listener, 8)) return 66;
    if (fork() == 0) { if (prctl(PR_SET_PDEATHSIG, SIGTERM) || getppid() == 1) return 67; serve(listener, socket_path, relay_fd); return 0; }
    close(listener);
  }
  close_nonstandard_fds();
  execv(argv[command], &argv[command]);
  return 68;
}
