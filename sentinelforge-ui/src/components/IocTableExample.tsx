import React from "react";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

interface IOC {
  id: string;
  value: string;
  type: string;
  severity: string;
}

const iocData: IOC[] = [
  { id: "1", value: "example.com", type: "domain", severity: "high" },
  { id: "2", value: "malware.exe", type: "file", severity: "critical" },
  { id: "3", value: "192.168.1.1", type: "ip", severity: "medium" },
];

export function IocTableExample() {
  return (
    <Table>
      <TableCaption>List of IOC indicators</TableCaption>
      <TableHeader>
        <TableRow>
          <TableHead>Value</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Severity</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {iocData.map((ioc) => (
          <TableRow key={ioc.id}>
            <TableCell className="text-gray-100">{ioc.value}</TableCell>
            <TableCell>{ioc.type}</TableCell>
            <TableCell>{ioc.severity}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
