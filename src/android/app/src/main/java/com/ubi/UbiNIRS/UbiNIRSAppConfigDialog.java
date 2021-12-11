package com.ubi.UbiNIRS;

import android.app.AlertDialog;
import android.app.Dialog;
import android.app.DialogFragment;
import android.content.Context;
import android.content.DialogInterface;
import android.graphics.Color;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Patterns;
import android.view.LayoutInflater;
import android.webkit.URLUtil;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import com.ubi.NanoScan.R;

public class UbiNIRSAppConfigDialog extends DialogFragment {

    private Context mContext;

    private boolean isAddressValid;
//    private boolean isPortValid;

    // Spinner for choosing http type.
    Spinner sp_type;
    ArrayAdapter<CharSequence> adapter;

    TextView tv_address;
    EditText et_address;

    @Override
    public Dialog onCreateDialog(Bundle savedInstanceState) {
        AlertDialog.Builder builder = new AlertDialog.Builder(getActivity());
        // Get the layout inflater
        LayoutInflater inflater = getActivity().getLayoutInflater();

        // Inflate and set the layout for the dialog
        // Pass null as the parent view because its going in the dialog layout
        builder.setTitle(R.string.dialog_title);
        builder.setView(inflater.inflate(R.layout.dialog_nirsapp_config, null))
                .setPositiveButton(R.string.dialog_confirm, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialogInterface, int i) {
                        listener.onDialogPositiveClick(UbiNIRSAppConfigDialog.this);
                    }
                })
                .setNegativeButton(R.string.dialog_cancel, new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialogInterface, int i) {
                        listener.onDialogNegativeClick(UbiNIRSAppConfigDialog.this);
                    }
                });
        return builder.create();
    }

    /* The activity that creates an instance of this dialog fragment must
     * implement this interface in order to receive event callbacks.
     * Each method passes the DialogFragment in case the host needs to query it. */
    public interface NoticeDialogListener {
        void onDialogPositiveClick(DialogFragment dialog);
        void onDialogNegativeClick(DialogFragment dialog);
    }

    // Use this instance of the interface to deliver action events
    NoticeDialogListener listener;

    // Override the Fragment.onAttach() method to instantiate the NoticeDialogListener
    @Override
    public void onAttach(Context context) {
        super.onAttach(context);

        mContext = context;

        // Verify that the host activity implements the callback interface
        try {
            // Instantiate the NoticeDialogListener so we can send events to the host
            listener = (NoticeDialogListener) context;
        } catch (ClassCastException e) {
            // The activity doesn't implement the interface, throw exception
            throw new ClassCastException(getActivity().toString()
                    + " must implement NoticeDialogListener.");
        }
    }

    @Override
    public void onStart() {
        super.onStart();
        getDialog().setCanceledOnTouchOutside(false);

        // Add input check.
        isAddressValid = false;
//        isPortValid = false;
        switchConfimButton(false);

        // Set spinner for choosing Http / https.
        adapter = ArrayAdapter.createFromResource(
                mContext, R.array.dialog_http_methods, android.R.layout.simple_dropdown_item_1line);
        sp_type = getDialog().findViewById(R.id.sp_httptype);
        sp_type.setAdapter(adapter);
        sp_type.setSelection(0);


        // Find text views.
        tv_address = getDialog().findViewById(R.id.tv_address);
        et_address = getDialog().findViewById(R.id.et_address);

        // Address check.
        ((EditText) getDialog().findViewById(R.id.et_address)).addTextChangedListener(new TextWatcher() {
            @Override
            public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {
                // Do nothing.
            }

            @Override
            public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {
                // Check if address is valid.
                if(charSequence.length() == 0) {
                    return;
                }

                // Get the inputs.
                String url = charSequence.toString();

                // Address sanity check.
                if((!Patterns.WEB_URL.matcher(url).matches()) & (!Patterns.IP_ADDRESS.matcher(url).matches())) {
                    // Not a valid URL nor IP.
                    tv_address.setText(R.string.dialog_address_invalid);
                    tv_address.setTextColor(Color.RED);
                    isAddressValid = false;
                }
                else {
                    // Valid URL or IP.
                    tv_address.setText(R.string.dialog_address_title);
                    tv_address.setTextColor(Color.BLACK);
                    isAddressValid = true;
                }

                switchConfimButton(isAddressValid);
            }

            @Override
            public void afterTextChanged(Editable editable) {
                // Do nothing.
            }
        });

        // Port check.
//        ((EditText) getDialog().findViewById(R.id.et_port)).addTextChangedListener(new TextWatcher() {
//            @Override
//            public void beforeTextChanged(CharSequence charSequence, int i, int i1, int i2) {
//                // Do nothing.
//            }
//
//            @Override
//            public void onTextChanged(CharSequence charSequence, int i, int i1, int i2) {
//                // Check if port number is valid.
//                if(charSequence.length() == 0) {
//                    return;
//                }
//
//                // Get the inputs.
//                int iPort = Integer.parseInt(charSequence.toString());
//
//                // Address sanity check.
//                if((iPort < 1) | (iPort > 65535)) {
//                    // Not a port number
//                    tv_port.setText(R.string.dialog_port_invalid);
//                    tv_port.setTextColor(Color.RED);
//                    isPortValid = false;
//                }
//                else {
//                    // Valid URL or IP.
//                    tv_port.setText(R.string.dialog_port_title);
//                    tv_port.setTextColor(Color.BLACK);
//                    isPortValid = true;
//                }
//
//                switchConfimButton(isAddressValid & isPortValid);
//            }
//
//            @Override
//            public void afterTextChanged(Editable editable) {
//                // Do nothing.
//            }
//        });
    }

    private void switchConfimButton(boolean isEnabled) {
        ((AlertDialog) getDialog()).getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(isEnabled);
    }
}
