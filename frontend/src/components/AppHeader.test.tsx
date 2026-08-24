import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ThemeProvider } from "./ThemeProvider";
import { AppHeader } from "./AppHeader";

function renderHeader(status: "loading" | "live" | "offline") {
  return render(
    <ThemeProvider>
      <AppHeader status={status} />
    </ThemeProvider>,
  );
}

describe("AppHeader API badge", () => {
  it("renders a muted connecting chip while loading", () => {
    renderHeader("loading");
    expect(screen.getByText("connecting")).toBeInTheDocument();
    expect(screen.queryByText("api offline")).toBeNull();
    expect(screen.queryByText("api live")).toBeNull();
  });

  it("renders api live when status is live", () => {
    renderHeader("live");
    expect(screen.getByText("api live")).toBeInTheDocument();
    expect(screen.queryByText("connecting")).toBeNull();
    expect(screen.queryByText("api offline")).toBeNull();
  });

  it("renders api offline when status is offline", () => {
    renderHeader("offline");
    expect(screen.getByText("api offline")).toBeInTheDocument();
    expect(screen.queryByText("connecting")).toBeNull();
    expect(screen.queryByText("api live")).toBeNull();
  });
});
