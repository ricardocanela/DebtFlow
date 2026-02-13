import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface WorklistState {
  selectedAccountId: string | null;
  selectedRowIndex: number;
}

const initialState: WorklistState = {
  selectedAccountId: null,
  selectedRowIndex: -1,
};

const worklistSlice = createSlice({
  name: 'worklist',
  initialState,
  reducers: {
    setSelectedAccount(state, action: PayloadAction<string | null>) {
      state.selectedAccountId = action.payload;
    },
    setSelectedRowIndex(state, action: PayloadAction<number>) {
      state.selectedRowIndex = action.payload;
    },
  },
});

export const { setSelectedAccount, setSelectedRowIndex } = worklistSlice.actions;
export default worklistSlice.reducer;
