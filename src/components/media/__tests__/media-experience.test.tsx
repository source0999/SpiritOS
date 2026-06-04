// @vitest-environment jsdom
import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { MediaExperience } from "@/components/media/MediaExperience";

describe("MediaExperience", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  function showDevEvidence() {
    fireEvent.click(screen.getByRole("button", { name: /show dev \/ evidence/i }));
  }

  it("renders the isolated media POC shell and key sections", () => {
    render(<MediaExperience />);

    expect(
      screen.getByRole("heading", { name: "Media", level: 1 }),
    ).toBeInTheDocument();
    expect(screen.getByText(/local proof of concept/i)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /local mock profile gate/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Continue Watching" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Watchlist" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Library" })).toBeInTheDocument();
    expect(screen.getAllByRole("heading", { name: "They Were Right" }).length).toBeGreaterThan(0);
    expect(screen.getByText(/Source contract:/i)).toBeInTheDocument();
    expect(screen.getByText("public/media/they-were-right.mp4")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /show dev \/ evidence/i })).toBeInTheDocument();
  });

  it("renders manual local movie cards and existing demo entries", () => {
    render(<MediaExperience />);

    expect(screen.getAllByText("They Were Right").length).toBeGreaterThan(0);
    expect(screen.getByText("Survivors of Saturn")).toBeInTheDocument();
    expect(screen.getByText("Kabbalah Intro")).toBeInTheDocument();
    expect(screen.getByText("Jesus Was Not a Christian")).toBeInTheDocument();
    expect(screen.getAllByText("Local Lights").length).toBeGreaterThan(0);
    expect(screen.getByText("Workbench Weekend")).toBeInTheDocument();
    expect(screen.getByText("Pilot Light")).toBeInTheDocument();
    expect(screen.getByText("Second Signal")).toBeInTheDocument();
    expect(screen.getByText("Signal House")).toBeInTheDocument();
    expect(screen.getAllByText(/Local Library/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Ready for owned file/i)).toBeInTheDocument();
  });

  it("loads each manual local movie card into the native player with the correct source path", () => {
    render(<MediaExperience />);

    const cases = [
      ["They Were Right", "/media/they-were-right.mp4"],
      ["Survivors of Saturn", "/media/survivors-of-saturn.mp4"],
      ["Kabbalah Intro", "/media/kabbalah-intro.mp4"],
      ["Jesus Was Not a Christian", "/media/jesus-was-not-a-christian.mp4"],
    ] as const;

    const video = () => document.querySelector("video") as HTMLVideoElement;

    for (const [title, sourcePath] of cases) {
      fireEvent.click(screen.getByRole("button", { name: `Open ${title}` }));

      expect(screen.getByRole("heading", { name: title, level: 2 })).toBeInTheDocument();
      expect(video().getAttribute("src")).toBe(sourcePath);
    }
  });

  it("shows profile switching state", () => {
    render(<MediaExperience />);

    fireEvent.click(screen.getByRole("button", { name: "Friend" }));

    expect(screen.getByText(/Selected profile:/i)).toHaveTextContent("Friend");
  });

  it("offers watchlist controls and an empty Continue Watching state", () => {
    render(<MediaExperience />);

    expect(
      screen.getByText(/Play or seek in an authorized local sample video/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("button", { name: /add to watchlist/i }).length,
    ).toBeGreaterThan(0);
  });

  it("shows local media source hardening guidance", () => {
    render(<MediaExperience />);

    expect(
      screen.getByLabelText(/local media source contract/i),
    ).toHaveTextContent("authorized sample file");
    expect(screen.getAllByText(/Waiting to load/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(/No copyrighted, downloaded, pirated, or binary media files/i),
    ).toBeInTheDocument();
  });

  it("shows the Phase 3 local library acceptance shape", () => {
    render(<MediaExperience />);
    showDevEvidence();

    expect(
      screen.getByLabelText(/local library acceptance plan/i),
    ).toHaveTextContent("Metadata is manually curated");
    expect(screen.getByText(/Each playable item has year/i)).toBeInTheDocument();
    expect(screen.getByText(/manual public media match strategy/i)).toBeInTheDocument();
  });

  it("shows the Phase 5 browser acceptance checklist", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const checklist = screen.getByLabelText(
      /local media browser acceptance checklist/i,
    );
    expect(checklist).toHaveTextContent("/media/*.mp4");
    expect(checklist).toHaveTextContent("only one nav is visible");
    expect(checklist).toHaveTextContent("phone width");
    expect(checklist).toHaveTextContent(
      "watchlist, progress, and curation checks stay separate",
    );
  });

  it("shows the Phase 6 local persistence decision gate", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const decisionGate = screen.getByRole("region", {
      name: /local media persistence decision/i,
    });
    expect(decisionGate).toHaveTextContent(
      "keep this POC browser-local and code-cataloged",
    );
    expect(decisionGate).toHaveTextContent("Keep localStorage for the next loop");
    expect(decisionGate).toHaveTextContent("Keep the manual local catalog entries in code");
    expect(decisionGate).toHaveTextContent(
      "Database, API routes, filesystem scanning, and manifest import",
    );
  });

  it("records Phase 7 playback acceptance evidence per profile", () => {
    render(<MediaExperience />);

    const acceptancePanel = screen.getByLabelText(
      /local sample playback acceptance/i,
    );
    expect(acceptancePanel).toHaveTextContent("profile-local notes");
    expect(acceptancePanel).toHaveTextContent("Evidence remains incomplete");

    for (const checkbox of within(acceptancePanel).getAllByRole("checkbox")) {
      fireEvent.click(checkbox);
    }

    expect(acceptancePanel).toHaveTextContent(
      "Playback acceptance evidence saved locally for this profile.",
    );

    fireEvent.click(screen.getByRole("button", { name: "Friend" }));
    expect(
      screen.getByLabelText(/local sample playback acceptance/i),
    ).toHaveTextContent("Evidence remains incomplete");
  });

  it("shows a read-only Phase 9 readiness summary for the active profile and item", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const readinessSummary = screen.getByRole("region", {
      name: /local media readiness summary/i,
    });
    expect(readinessSummary).toHaveTextContent("Britton");
    expect(readinessSummary).toHaveTextContent("They Were Right");
    expect(readinessSummary).toHaveTextContent("public/media/they-were-right.mp4");
    expect(readinessSummary).toHaveTextContent(
      "Waiting on manual confirmation",
    );
    expect(readinessSummary).toHaveTextContent("Waiting on browser playback");
    expect(readinessSummary).toHaveTextContent("No saved timestamp");
    expect(readinessSummary).toHaveTextContent("Waiting to load");
    expect(readinessSummary).toHaveTextContent("Runtime read source");
    expect(readinessSummary).toHaveTextContent("Local fallback");
    expect(readinessSummary).toHaveTextContent("Profile write path");
    expect(readinessSummary).toHaveTextContent("Not attempted");
    expect(readinessSummary).toHaveTextContent("Primary profile state");
    expect(readinessSummary).toHaveTextContent("Blocked");
  });

  it("reports Dexie profile-state side write status after a local action", async () => {
    render(<MediaExperience />);
    showDevEvidence();

    const library = screen.getByRole("heading", { name: "Library" }).closest("section");
    expect(library).not.toBeNull();

    fireEvent.click(
      within(library as HTMLElement).getAllByRole("button", {
        name: /add to watchlist/i,
      })[0],
    );

    const readinessSummary = screen.getByRole("region", {
      name: /local media readiness summary/i,
    });
    expect(
      await within(readinessSummary).findByText("Dexie unavailable"),
    ).toBeInTheDocument();
  });

  it("keeps the Phase 10 browser polish controls available", () => {
    render(<MediaExperience />);

    expect(
      screen.getByRole("button", { name: /reset current profile state/i }),
    ).toBeInTheDocument();
    expect(
      screen.getAllByRole("button", { name: /add to watchlist/i }).length,
    ).toBeGreaterThan(0);
    expect(screen.getByLabelText(/current profile reset control/i)).toHaveTextContent(
      "other profiles stay untouched",
    );
  });

  it("shows the Phase 11 local media acceptance freeze", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const freezePanel = screen.getByRole("region", {
      name: /local media acceptance freeze/i,
    });
    expect(freezePanel).toHaveTextContent("Plan 1 freezes here");
    expect(freezePanel).toHaveTextContent("Profiles remain local mock profiles");
    expect(freezePanel).toHaveTextContent("Catalog remains manual source-code entries");
    expect(freezePanel).toHaveTextContent(
      "No database, API route, scanner, PWA, transcoder, or committed media binary",
    );
  });

  it("runs the manual IndexedDB harness only from the explicit UI control", async () => {
    render(<MediaExperience />);
    showDevEvidence();

    const harnessPanel = screen.getByRole("region", {
      name: /manual indexeddb acceptance harness/i,
    });
    expect(harnessPanel).toHaveTextContent("Not run");
    expect(harnessPanel).toHaveTextContent("No automatic migration runs");

    fireEvent.click(
      within(harnessPanel).getByRole("button", {
        name: /run manual indexeddb check/i,
      }),
    );

    expect(
      await within(harnessPanel).findByText(/Latest manual report:/i),
    ).toHaveTextContent("Needs browser run");
    expect(harnessPanel).toHaveTextContent("Not confirmed");
    expect(harnessPanel).toHaveTextContent("Not migrated");
  });

  it("shows a read-only manual IndexedDB evidence summary", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const evidenceSummary = screen.getByRole("region", {
      name: /manual indexeddb evidence summary/i,
    });
    expect(evidenceSummary).toHaveTextContent("Blocked");
    expect(evidenceSummary).toHaveTextContent("Not run");
    expect(evidenceSummary).toHaveTextContent("Local fallback");
    expect(evidenceSummary).toHaveTextContent("Not attempted");
    expect(evidenceSummary).toHaveTextContent("Manual DevTools check required");
    expect(evidenceSummary).toHaveTextContent("Preserved");
    expect(evidenceSummary).toHaveTextContent("Not reviewed");
    expect(evidenceSummary).toHaveTextContent("does not promote storage");
  });

  it("shows manual browser run capture notes without saving them in the app", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const runNotes = screen.getByRole("region", {
      name: /browser run capture notes/i,
    });
    expect(runNotes).toHaveTextContent("Manual note template");
    expect(runNotes).toHaveTextContent("not saved by the app");
    expect(runNotes).toHaveTextContent("Browser and version");
    expect(runNotes).toHaveTextContent("Manual report");
    expect(runNotes).toHaveTextContent("IndexedDB tables");
    expect(runNotes).toHaveTextContent("Fallback check");
    expect(runNotes).toHaveTextContent("Stop conditions");
    expect(within(runNotes).getAllByText("Required").length).toBe(8);
    expect(within(runNotes).getByText("Optional")).toBeInTheDocument();
  });

  it("shows the Dexie primary profile-state promotion decision as no-go by default", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const promotionDecision = screen.getByRole("region", {
      name: /dexie primary profile-state decision/i,
    });
    expect(promotionDecision).toHaveTextContent("Do not promote");
    expect(promotionDecision).toHaveTextContent("Manual evidence");
    expect(promotionDecision).toHaveTextContent("Blocked");
    expect(promotionDecision).toHaveTextContent("Approval");
    expect(promotionDecision).toHaveTextContent("Missing");
    expect(promotionDecision).toHaveTextContent("Rollback");
    expect(promotionDecision).toHaveTextContent("Not confirmed");
    expect(promotionDecision).toHaveTextContent("Primary source");
    expect(promotionDecision).toHaveTextContent("localStorage");
  });

  it("shows the browser evidence archive packet as a read-only draft", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const archivePacket = screen.getByRole("region", {
      name: /browser evidence archive packet/i,
    });
    expect(archivePacket).toHaveTextContent("Draft");
    expect(archivePacket).toHaveTextContent("Manual evidence");
    expect(archivePacket).toHaveTextContent("Blocked");
    expect(archivePacket).toHaveTextContent("Promotion decision");
    expect(archivePacket).toHaveTextContent("Do not promote");
    expect(archivePacket).toHaveTextContent("Run notes");
    expect(archivePacket).toHaveTextContent("Not captured");
    expect(archivePacket).toHaveTextContent("Archive location");
    expect(archivePacket).toHaveTextContent("Not recorded");
    expect(archivePacket).toHaveTextContent("Media binaries");
    expect(archivePacket).toHaveTextContent("excluded");
  });

  it("shows the browser evidence export decision as manual no-go by default", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const exportDecision = screen.getByRole("region", {
      name: /browser evidence export decision/i,
    });
    expect(exportDecision).toHaveTextContent("Do not export");
    expect(exportDecision).toHaveTextContent("Archive packet");
    expect(exportDecision).toHaveTextContent("Draft");
    expect(exportDecision).toHaveTextContent("Approval");
    expect(exportDecision).toHaveTextContent("Missing");
    expect(exportDecision).toHaveTextContent("Export location");
    expect(exportDecision).toHaveTextContent("Not selected");
    expect(exportDecision).toHaveTextContent("Export method");
    expect(exportDecision).toHaveTextContent("Manual only");
    expect(exportDecision).toHaveTextContent("does not write files");
  });

  it("shows an evidence packet manual copy template without app export behavior", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const copyTemplate = screen.getByRole("region", {
      name: /evidence packet manual copy template/i,
    });
    expect(copyTemplate).toHaveTextContent("not saved");
    expect(copyTemplate).toHaveTextContent("downloaded");
    expect(copyTemplate).toHaveTextContent("copied to the clipboard");
    expect(copyTemplate).toHaveTextContent("Manual Evidence");
    expect(copyTemplate).toHaveTextContent("Status: blocked");
    expect(copyTemplate).toHaveTextContent("Promotion Decision");
    expect(copyTemplate).toHaveTextContent("Status: do-not-promote");
    expect(copyTemplate).toHaveTextContent("Archive Packet");
    expect(copyTemplate).toHaveTextContent("Status: draft");
    expect(copyTemplate).toHaveTextContent("Export Decision");
    expect(copyTemplate).toHaveTextContent("Status: do-not-export");
    expect(copyTemplate).toHaveTextContent("Dexie primary profile-state promotion");
  });

  it("shows a manual browser fill-in procedure for the evidence packet", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const fillProcedure = screen.getByRole("region", {
      name: /evidence packet manual fill-in procedure/i,
    });
    expect(fillProcedure).toHaveTextContent("Manual browser procedure");
    expect(fillProcedure).toHaveTextContent("Nothing here is saved");
    expect(fillProcedure).toHaveTextContent("Prepare browser state");
    expect(fillProcedure).toHaveTextContent("Run manual IndexedDB check");
    expect(fillProcedure).toHaveTextContent("Inspect DevTools tables");
    expect(fillProcedure).toHaveTextContent("Fill copy template");
    expect(fillProcedure).toHaveTextContent("Review blockers");
    expect(fillProcedure).toHaveTextContent("Record archive location");
    expect(fillProcedure).toHaveTextContent("without attaching media binaries");
  });

  it("shows a browser manual run checklist for the evidence packet", () => {
    render(<MediaExperience />);
    showDevEvidence();

    const runChecklist = screen.getByRole("region", {
      name: /evidence packet browser manual run checklist/i,
    });
    expect(runChecklist).toHaveTextContent("Manual checklist");
    expect(runChecklist).toHaveTextContent("does not store checklist results");
    expect(runChecklist).toHaveTextContent("Open /media in a real browser");
    expect(runChecklist).toHaveTextContent("Run manual IndexedDB check");
    expect(runChecklist).toHaveTextContent("Inspect DevTools SpiritMediaDB tables");
    expect(runChecklist).toHaveTextContent("Verify localStorage fallback");
    expect(runChecklist).toHaveTextContent("Fill manual copy template");
    expect(runChecklist).toHaveTextContent("Record archive location");
    expect(runChecklist).toHaveTextContent(/no media binaries/i);
    expect(within(runChecklist).getAllByText("Required").length).toBe(9);
  });

  it("resets only the current profile media state", () => {
    render(<MediaExperience />);

    const library = screen.getByRole("heading", { name: "Library" }).closest("section");
    expect(library).not.toBeNull();

    fireEvent.click(
      within(library as HTMLElement).getAllByRole("button", {
        name: /add to watchlist/i,
      })[0],
    );

    const curationPanel = screen.getByLabelText(/manual local library curation/i);
    fireEvent.click(
      within(curationPanel).getByRole("checkbox", {
        name: /confirmed this authorized local file path/i,
      }),
    );

    const acceptancePanel = screen.getByLabelText(
      /local sample playback acceptance/i,
    );
    for (const checkbox of within(acceptancePanel).getAllByRole("checkbox")) {
      fireEvent.click(checkbox);
    }

    fireEvent.click(screen.getByRole("button", { name: "Friend" }));
    const friendLibrary = screen
      .getByRole("heading", { name: "Library" })
      .closest("section");
    expect(friendLibrary).not.toBeNull();
    fireEvent.click(
      within(friendLibrary as HTMLElement).getAllByRole("button", {
        name: /add to watchlist/i,
      })[0],
    );

    fireEvent.click(screen.getByRole("button", { name: "Britton" }));
    fireEvent.click(
      screen.getByRole("button", { name: /reset current profile state/i }),
    );

    const watchlist = screen
      .getByRole("heading", { name: "Watchlist" })
      .closest("section");
    expect(watchlist).not.toBeNull();
    expect(watchlist).toHaveTextContent("Empty");
    expect(screen.getByLabelText(/manual local library curation/i)).toHaveTextContent(
      "does not scan the filesystem",
    );
    expect(
      screen.getByLabelText(/local sample playback acceptance/i),
    ).toHaveTextContent("Evidence remains incomplete");

    fireEvent.click(screen.getByRole("button", { name: "Friend" }));
    const friendWatchlist = screen
      .getByRole("heading", { name: "Watchlist" })
      .closest("section");
    expect(friendWatchlist).not.toBeNull();
    expect(within(friendWatchlist as HTMLElement).getByText("They Were Right")).toBeInTheDocument();
  });

  it("saves a manual curation check per profile", () => {
    render(<MediaExperience />);

    const curationPanel = screen.getByLabelText(/manual local library curation/i);
    expect(curationPanel).toHaveTextContent("they-were-right.mp4");
    expect(curationPanel).toHaveTextContent("does not scan the filesystem");

    fireEvent.click(
      within(curationPanel).getByRole("checkbox", {
        name: /confirmed this authorized local file path/i,
      }),
    );

    expect(curationPanel).toHaveTextContent(
      "Curation check saved locally for this profile.",
    );

    fireEvent.click(screen.getByRole("button", { name: "Friend" }));
    expect(
      screen.getByLabelText(/manual local library curation/i),
    ).toHaveTextContent("does not scan the filesystem");
  });

  it("adds a catalog item to the current profile Watchlist", () => {
    render(<MediaExperience />);

    const library = screen.getByRole("heading", { name: "Library" }).closest("section");
    expect(library).not.toBeNull();

    fireEvent.click(
      within(library as HTMLElement).getAllByRole("button", {
        name: /add to watchlist/i,
      })[0],
    );

    const watchlist = screen
      .getByRole("heading", { name: "Watchlist" })
      .closest("section");
    expect(watchlist).not.toBeNull();
    expect(within(watchlist as HTMLElement).getByText("They Were Right")).toBeInTheDocument();
  });
});
