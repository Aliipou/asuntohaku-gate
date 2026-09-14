import "@testing-library/jest-dom/vitest";

import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// vitest.config.mts doesn't set `test.globals`, so @testing-library/react's
// own auto-cleanup (which only registers when it finds a global `afterEach`)
// never fires. Without this, component tests accumulate DOM across every
// `it()` in a file — a later test's queryByText/queryByRole can match a
// previous test's leftover render instead of (or as well as) its own.
afterEach(cleanup);
