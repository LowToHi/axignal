"use client";

import {
  OperationsWorkspace as BaseOperationsWorkspace,
  TenderOperationsWorkspace as BaseTenderOperationsWorkspace,
  type OperationsWorkspaceProps
} from "./tender-operations-workspace";
import { provenanceSafeOperationsData } from "./operations-provenance";
import type { TenderOperationsWorkspaceProps } from "./types";

const REAL_ADAPTER_BOUNDARY =
  "Live-adapter mode withholds documents, team, approvals, amendment impact and derived readiness until each projection carries persistent provenance.";

export function TenderOperationsWorkspace(props: TenderOperationsWorkspaceProps) {
  if (!props.data || props.data.fixtureMode === true) {
    return <BaseTenderOperationsWorkspace {...props} />;
  }

  return (
    <BaseTenderOperationsWorkspace
      {...props}
      data={provenanceSafeOperationsData(props.data)}
      state={props.state === "ready" ? "partial" : props.state}
      stateMessage={props.stateMessage ?? REAL_ADAPTER_BOUNDARY}
    />
  );
}

export function OperationsWorkspace(props: OperationsWorkspaceProps) {
  if (!props.data || props.data.fixtureMode === true) {
    return <BaseOperationsWorkspace {...props} />;
  }

  return (
    <BaseOperationsWorkspace
      {...props}
      data={provenanceSafeOperationsData(props.data)}
      state={props.state === "ready" ? "partial" : props.state}
      stateMessage={props.stateMessage ?? REAL_ADAPTER_BOUNDARY}
    />
  );
}

export type { OperationsActionPayload, OperationsWorkspaceProps } from "./tender-operations-workspace";
