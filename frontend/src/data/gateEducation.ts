export interface GateEducation {
  name: string;
  plainEnglish: string;
  blochHint: string;
  example: string;
}

const education: GateEducation[] = [
  {
    name: 'H',
    plainEnglish: 'Creates equal superposition — the qubit has a 50/50 chance of being 0 or 1.',
    blochHint: 'The arrow rotates from pointing up (|0>) to pointing sideways along the X-axis.',
    example: 'Like flipping a perfectly fair coin.',
  },
  {
    name: 'X',
    plainEnglish: 'Flips the qubit — turns |0> into |1> and |1> into |0>.',
    blochHint: 'The arrow flips from the north pole to the south pole (or vice versa).',
    example: 'Like a classical NOT gate or a light switch.',
  },
  {
    name: 'Y',
    plainEnglish: 'Flips the qubit and adds a phase shift. Combines a bit flip with a phase flip.',
    blochHint: 'Rotates the arrow 180 degrees around the Y-axis of the Bloch sphere.',
    example: 'Like flipping a coin and also marking which side was up.',
  },
  {
    name: 'Z',
    plainEnglish: 'Adds a phase flip — |1> picks up a minus sign. Does not change measurement probabilities alone.',
    blochHint: 'Rotates the arrow 180 degrees around the Z-axis (flips X and Y components).',
    example: 'Like changing the hidden "phase" of a wave without changing its height.',
  },
  {
    name: 'S',
    plainEnglish: 'Adds a 90-degree phase rotation. Like a quarter of a Z gate.',
    blochHint: 'Rotates the arrow 90 degrees around the Z-axis on the equator.',
    example: 'A quarter-turn of the phase dial.',
  },
  {
    name: 'T',
    plainEnglish: 'Adds a 45-degree phase rotation. Essential for fault-tolerant quantum computing.',
    blochHint: 'Rotates the arrow 45 degrees around the Z-axis.',
    example: 'An eighth-turn of the phase dial — small but crucial for complex algorithms.',
  },
  {
    name: 'Sdg',
    plainEnglish: 'Reverses the S gate — rotates phase by -90 degrees.',
    blochHint: 'Rotates the arrow -90 degrees around the Z-axis.',
    example: 'Undoes what the S gate did.',
  },
  {
    name: 'Tdg',
    plainEnglish: 'Reverses the T gate — rotates phase by -45 degrees.',
    blochHint: 'Rotates the arrow -45 degrees around the Z-axis.',
    example: 'Undoes what the T gate did.',
  },
  {
    name: 'SX',
    plainEnglish: 'Half of an X gate — partially flips the qubit into a superposition.',
    blochHint: 'Rotates the arrow 90 degrees around the X-axis.',
    example: 'Like half-pressing a light switch.',
  },
  {
    name: 'Rx',
    plainEnglish: 'Rotates the qubit around the X-axis by a chosen angle.',
    blochHint: 'The arrow spins around the X-axis by the angle you specify.',
    example: 'Like tilting a spinning top sideways by a precise amount.',
  },
  {
    name: 'Ry',
    plainEnglish: 'Rotates the qubit around the Y-axis by a chosen angle.',
    blochHint: 'The arrow spins around the Y-axis — smoothly moves between |0> and |1>.',
    example: 'Smoothly dials between "definitely 0" and "definitely 1".',
  },
  {
    name: 'Rz',
    plainEnglish: 'Rotates the qubit around the Z-axis by a chosen angle.',
    blochHint: 'The arrow spins around the Z-axis — changes phase without changing probabilities.',
    example: 'Like adjusting the timing of a wave without changing its height.',
  },
  {
    name: 'P',
    plainEnglish: 'Applies a phase shift to the |1> state by a chosen angle.',
    blochHint: 'Rotates the arrow around the Z-axis, only affecting the phase of |1>.',
    example: 'Fine-tunes the "hidden angle" of the qubit state.',
  },
  {
    name: 'CNOT',
    plainEnglish: 'Flips the target qubit only when the control qubit is |1>. Creates entanglement.',
    blochHint: 'Correlates two qubits — their Bloch vectors become linked and may shrink (mixed state).',
    example: 'Like a light switch that only works when another switch is ON.',
  },
  {
    name: 'CZ',
    plainEnglish: 'Flips the phase of |11> — both qubits must be |1> for the sign to change.',
    blochHint: 'Creates entanglement through phase — no visible flip, but the states are linked.',
    example: 'Two switches that together trigger a hidden phase change.',
  },
  {
    name: 'SWAP',
    plainEnglish: 'Exchanges the states of two qubits completely.',
    blochHint: 'The two qubit arrows trade places on their Bloch spheres.',
    example: 'Like swapping the contents of two boxes.',
  },
  {
    name: 'TOFFOLI',
    plainEnglish: 'Flips the target only when BOTH controls are |1>. A quantum AND gate.',
    blochHint: 'Three-qubit gate — the target flips only with two controls active.',
    example: 'A door that only opens when two different keys are turned at once.',
  },
];

const educationMap = new Map(education.map(e => [e.name, e]));

export function getGateEducation(gateName: string): GateEducation | undefined {
  return educationMap.get(gateName);
}

export default education;
