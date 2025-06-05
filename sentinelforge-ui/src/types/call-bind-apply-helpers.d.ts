// Type declaration override for call-bind-apply-helpers
// This fixes TypeScript 4.x compatibility issues with the package

declare module "call-bind-apply-helpers" {
  export function callBindBasic(
    fn: Function,
    thisArg?: any,
    ...boundArgs: any[]
  ): Function;
  export function callBind(
    fn: Function,
    thisArg?: any,
    ...boundArgs: any[]
  ): Function;
  export default function callBind(
    fn: Function,
    thisArg?: any,
    ...boundArgs: any[]
  ): Function;
}
