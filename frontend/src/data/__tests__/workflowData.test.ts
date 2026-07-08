import { describe, expect, it } from 'vitest'
import { workflowTabs } from '@/data/workflowData'

function findNode(id: string) {
  for (const tab of workflowTabs) {
    const node = tab.nodes.find((n) => n.id === id)
    if (node) return node
  }
  return undefined
}

describe('workflowData — reference dataset (Fabric)', () => {
  it('exposes the Microsoft Fabric technologies on the refdata node', () => {
    const refdata = findNode('refdata')
    expect(refdata).toBeDefined()
    const tech = refdata!.detail.technologies ?? []
    expect(tech).toContain('Microsoft Fabric Lakehouse')
    expect(tech).toContain('OneLake')
    expect(tech).toContain('Fabric SQL endpoint')
  })

  it('describes the Fabric Lakehouse → SQL endpoint data flow', () => {
    const refdata = findNode('refdata')
    const flow = (refdata!.detail.dataFlow ?? []).join(' ')
    expect(flow).toContain('Fabric Lakehouse')
    expect(flow).toContain('SQL endpoint')
  })
})
